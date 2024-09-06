from subroutine import *
from main_asa.note_signature import note_signature

note_type = "auction"


def contract_auction_main_asa():
    @Subroutine(TealType.none)
    def function_repay_bidder() -> Expr:
        return Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.Payment,
                    TxnField.amount: App.globalGet(bid_amount) - Global.min_txn_fee(),
                    TxnField.receiver: App.globalGet(bid_account),
                }
            ),
            InnerTxnBuilder.Submit(),
        )

    on_create = Seq(
        App.globalPut(asa_id, Btoi(Txn.application_args[0])),
        App.globalPut(nft_min_price, Btoi(Txn.application_args[1])),
        App.globalPut(end_time_key, Btoi(Txn.application_args[2])),
        App.globalPut(counter_party_address, Txn.application_args[3]),
        App.globalPut(counter_party_fees, Btoi(Txn.application_args[4])),
        App.globalPut(fees_address, Addr(FEES_ADDRESS)),
        App.globalPut(bid_account, Global.zero_address()),
        App.globalPut(late_bid_delay, Int(600)),
        App.globalPut(bid_amount, Int(0)),
        App.globalPut(main_fees, Int(2)),
        App.globalPut(fees_app_id, Int(FEES_APP_ID)),
        App.globalPut(note_address, Addr(NOTE_ADDRESS)),
        Approve(),
    )

    on_bid = Seq(
        Assert(
            And(
                Global.latest_timestamp() < App.globalGet(end_time_key),
                Gtxn[Txn.group_index() - Int(1)].type_enum() == TxnType.Payment,
                Gtxn[Txn.group_index() - Int(1)].receiver() == Global.current_application_address(),
                Gtxn[Txn.group_index() - Int(1)].amount() >= App.globalGet(nft_min_price),
                Gtxn[Txn.group_index() - Int(1)].amount() >= Div(Mul(App.globalGet(bid_amount), Int(110)), Int(100))
            )
        ),
        Seq(
            function_send_note(Int(ZERO_FEES), Bytes(f"{note_type},bid,{note_signature}")),
            If(
                App.globalGet(bid_account) != Global.zero_address()
            ).Then(
                function_repay_bidder()
            ),
            App.globalPut(bid_amount, Gtxn[Txn.group_index() - Int(1)].amount()),
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
        function_send_note(Int(PURCHASE_FEES), Bytes(f"{note_type},close,{note_signature}")),
        function_contract_fees(
            Div(
                Mul(
                    App.globalGet(bid_amount),
                    Add(
                        App.globalGet(main_fees),
                        App.globalGet(counter_party_fees)
                    )
                ),
                Int(100)
            ),
            Div(
                Mul(
                    App.globalGet(bid_amount),
                    App.globalGet(counter_party_fees)
                ),
                Int(100)
            )
        ),
        function_payment(
            Minus(
                App.globalGet(bid_amount),
                Div(
                    Mul(
                        App.globalGet(bid_amount),
                        Add(
                            App.globalGet(main_fees),
                            App.globalGet(counter_party_fees)
                        )
                    ),
                    Int(100)
                )
            )
        ),
        function_send_nft_asa(App.globalGet(bid_account), Int(1)),
        function_asa_optout(App.globalGet(asa_id)),
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
        function_close_app(),
        Approve()
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("fund")), on_fund_optin(f"{note_type},create,{note_signature}")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("pre_validate")), Approve()],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("bid")), on_bid],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("close")), on_close],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete_auction],
        completion_reject()
    )

    return program
