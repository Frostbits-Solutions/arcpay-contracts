from subroutine import *
from asa_asa.note_signature import note_signature

note_type = "auction"


def contract_auction_asa_asa():
    @Subroutine(TealType.none)
    def function_repay_bidder() -> Expr:
        return Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.AssetTransfer,
                    TxnField.xfer_asset: App.globalGet(paiment_asa_id),
                    TxnField.asset_receiver: App.globalGet(bid_account),
                    TxnField.asset_amount: App.globalGet(bid_amount) - Global.min_txn_fee(),
                    TxnField.fee: Global.min_txn_fee()
                }
            ),
            InnerTxnBuilder.Submit(),
        )

    on_create = Seq(
        App.globalPut(asa_id, Btoi(Txn.application_args[0])),
        App.globalPut(nft_min_price, Btoi(Txn.application_args[1])),
        App.globalPut(end_time_key, Btoi(Txn.application_args[2])),
        App.globalPut(counter_party_address, Txn.application_args[3]),
        App.globalPut(paiment_asa_id, Btoi(Txn.application_args[4])),
        initialisation_auction(),
        initialisation_smartcontract()
    )

    on_bid = Seq(
        Assert(
            And(
                Global.latest_timestamp() < App.globalGet(end_time_key),
                Gtxn[Txn.group_index() - Int(1)].type_enum() == TxnType.AssetTransfer,
                Gtxn[Txn.group_index() - Int(1)].asset_receiver() == Global.current_application_address(),
                Gtxn[Txn.group_index() - Int(1)].asset_amount() >= App.globalGet(nft_min_price),
                Gtxn[Txn.group_index() - Int(1)].asset_amount() >= Div(Mul(App.globalGet(bid_amount), Int(110)), Int(100)),
                Gtxn[Txn.group_index() - Int(1)].xfer_asset() == App.globalGet(paiment_asa_id)
            )
        ),
        Seq(
            function_send_note(Int(ZERO_FEES), Bytes(f"{note_type},bid,{note_signature}")),
            If(
                App.globalGet(bid_account) != Global.zero_address()
            ).Then(
                function_repay_bidder()
            ),
            App.globalPut(bid_amount, Gtxn[Txn.group_index() - Int(1)].asset_amount()),
            App.globalPut(bid_account, Gtxn[Txn.group_index() - Int(1)].sender()),
            If(
                Global.latest_timestamp() + App.globalGet(late_bid_delay) >= App.globalGet(end_time_key)
            ).Then(
                App.globalPut(end_time_key, (Global.latest_timestamp() + App.globalGet(late_bid_delay)))
            ),
            Approve(),
        )
    )

    on_close = Seq(
        Assert(
            And(
                App.globalGet(bid_account) != Global.zero_address(),
                App.globalGet(end_time_key) <= Global.latest_timestamp()
            )
        ),
        read_fees := App.globalGetEx(App.globalGet(fees_app_id), App.globalGet(counter_party_address)),
        function_send_note(Int(ZERO_FEES), Bytes(f"{note_type},close,{note_signature}")),
        function_contract_fees_asa(
            Div(
                Mul(
                    App.globalGet(bid_amount),
                    Add(
                        App.globalGet(main_fees),
                        read_fees.value()
                    )
                ),
                Int(100)
            ),
            Div(
                Mul(
                    App.globalGet(bid_amount),
                    read_fees.value()
                ),
                Int(100)
            )
        ),
        function_payment_asa(
            Minus(
                App.globalGet(bid_amount),
                Div(
                    Mul(
                        App.globalGet(bid_amount),
                        Add(
                            App.globalGet(main_fees),
                            read_fees.value()
                        )
                    ),
                    Int(100)
                )
            )
        ),
        function_send_nft_asa(App.globalGet(bid_account), Int(1)),
        function_asa_optout(App.globalGet(asa_id)),
        function_asa_optout(App.globalGet(paiment_asa_id)),
        function_close_app(),
        Approve()
    )

    on_delete_auction = Seq(
        Assert(
            Or(
                Txn.sender() == Global.creator_address(),
                Txn.sender() == App.globalGet(fees_address)
            )
        ),
        function_send_note(Int(ZERO_FEES), Bytes(f"{note_type},cancel,{note_signature}")),
        If(
            App.globalGet(bid_account) != Global.zero_address()
        ).Then(
            function_repay_bidder()
        ),
        function_asa_optout(App.globalGet(asa_id)),
        function_asa_optout(App.globalGet(paiment_asa_id)),
        function_close_app(),
        Approve()
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("fund")), on_fund_optin_asa(f"{note_type},create,{note_signature}")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("pre_validate")), Approve()],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("bid")), on_bid],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("close")), on_close],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete_auction],
        completion_reject()
    )

    return program
