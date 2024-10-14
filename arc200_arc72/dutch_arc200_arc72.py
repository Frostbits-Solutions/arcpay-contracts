from subroutine import *
from arc200_arc72.note_signature import note_signature

note_type = "dutch"


def contract_dutch_arc200_arc72(proxy_app_id):

    on_create = Seq(
        initialisation_arc72(0),
        initialisation_arc200(5),
        initialisation_dutch(2),
        initialisation_smartcontract(6, proxy_app_id)
    )

    on_buy = Seq(
        Assert(
            And(
                # formula to compute price is y = (((max-min)/(start-end)) * (current_time - start )) + max
                # new formula : max - (current-start)((max-min)/(end-start))
                Btoi(Txn.application_args[1]) >= Minus(
                    App.globalGet(nft_max_price),
                    Div(
                        Mul(
                            Minus(
                                App.globalGet(nft_max_price),
                                App.globalGet(nft_min_price)
                            ),
                            Minus(
                                Global.latest_timestamp(),
                                App.globalGet(start_time_key)
                            )
                        ),
                        Minus(
                            App.globalGet(end_time_key),
                            App.globalGet(start_time_key)
                        )
                    )
                ),
                Global.latest_timestamp() <= App.globalGet(end_time_key)
            )
        ),
        Seq(
            function_send_note(Int(ZERO_FEES), Bytes(f"{note_type},buy,{note_signature}")),
            function_contract_fees_arc200(Btoi(Txn.application_args[1])),
            function_fund_arc(arc200_app_address),
            function_transfer_arc200_end(Btoi(Txn.application_args[1])),
            function_fund_arc(nft_app_address),
            function_transfer_arc72(Txn.sender()),
            function_close_app(),
            Approve()
        ),
        Reject()
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete(f"{note_type},cancel,{note_signature}")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("fund")), on_fund(f"{note_type},create,{note_signature}")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("pre_validate")), Approve()],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("buy")), on_buy],
        completion_reject()
    )
    return program
