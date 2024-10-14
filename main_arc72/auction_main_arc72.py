from subroutine import *
from main_arc72.note_signature import note_signature

note_type = "auction"


def contract_auction_main_arc72(proxy_app_id):

    on_create = Seq(
        initialisation_arc72(0),
        initialisation_auction(2),
        initialisation_smartcontract(4, proxy_app_id)
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
                function_payment(App.globalGet(bid_amount), App.globalGet(bid_account))
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
        function_send_note(Int(ZERO_FEES), Bytes(f"{note_type},close,{note_signature}")),
        function_contract_fees(App.globalGet(bid_amount)),
        function_payment_manager(App.globalGet(bid_amount), function_payment),
        function_fund_arc(nft_app_address),
        function_transfer_arc72(App.globalGet(bid_account)),
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
            function_payment(App.globalGet(bid_amount), App.globalGet(bid_account))
        ),
        function_close_app(),
        Approve()
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("fund")), on_fund(f"{note_type},create,{note_signature}")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("pre_validate")), Approve()],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("bid")), on_bid],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("close")), on_close],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete_auction],
        completion_reject()
    )

    return program
