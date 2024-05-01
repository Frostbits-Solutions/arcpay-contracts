from pyteal import *
from constants import FEES_ADDRESS, PURCHASE_FEES
from subroutine import nft_id, nft_app_id, fees_address, arc200_app_id, arc200_app_address
from subroutine import function_transfer_arc72, function_fund_arc200, function_send_note, function_transfer_arc200
from subroutine import on_fund, on_delete, nft_max_price, nft_min_price, start_time_key, end_time_key


def approval_program():

    on_create = Seq(
        App.globalPut(nft_app_id, Btoi(Txn.application_args[0])),
        App.globalPut(nft_id, Txn.application_args[1]),
        App.globalPut(nft_max_price, Btoi(Txn.application_args[2])),
        App.globalPut(nft_min_price, Btoi(Txn.application_args[3])),
        App.globalPut(end_time_key, Btoi(Txn.application_args[4])),
        App.globalPut(arc200_app_id, Btoi(Txn.application_args[5])),
        App.globalPut(arc200_app_address, Txn.application_args[6]),
        App.globalPut(start_time_key, Global.latest_timestamp()),
        App.globalPut(fees_address, Addr(FEES_ADDRESS)),
        Assert(App.globalGet(nft_max_price) > App.globalGet(nft_min_price)),
        Assert(App.globalGet(end_time_key) > App.globalGet(start_time_key)),
        Approve(),
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
            function_fund_arc200(),
            function_transfer_arc200(Btoi(Txn.application_args[1])-Int(PURCHASE_FEES), Global.creator_address()),
            function_transfer_arc72(Txn.sender()),
            function_send_note(Int(PURCHASE_FEES), Bytes("dutch,buy,200/72")),
            Approve()
        ),
        Reject()
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete("dutch,cancel,200/72")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("fund")), on_fund("dutch,create,200/72")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("pre_validate")), Approve()],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("buy")), on_buy],
        [
            Or(
                Txn.on_completion() == OnComplete.OptIn,
                Txn.on_completion() == OnComplete.CloseOut,
                Txn.on_completion() == OnComplete.UpdateApplication
            ),
            Reject(),
        ],
    )
    return program
