from pyteal import *
from constants import FEES_ADDRESS, PURCHASE_FEES
from subroutine import function_send_note, function_transfer_arc72, function_fund_arc200, function_transfer_arc200, function_close_app
from subroutine import fees_address, nft_app_id, nft_id, arc200_app_address, arc200_app_id, price
from subroutine import on_fund, on_delete, on_update


def approval_program():

    on_create = Seq(
        App.globalPut(nft_app_id, Btoi(Txn.application_args[0])),
        App.globalPut(nft_id, Txn.application_args[1]),
        App.globalPut(price, Btoi(Txn.application_args[2])),
        App.globalPut(arc200_app_id, Btoi(Txn.application_args[3])),
        App.globalPut(arc200_app_address, Txn.application_args[4]),
        App.globalPut(fees_address, Addr(FEES_ADDRESS)),
        Approve(),
    )

    on_buy = Seq(
        Seq(
            function_send_note(Int(PURCHASE_FEES), Bytes("sale,buy,200/72")),
            function_fund_arc200(),
            function_transfer_arc200(App.globalGet(price)-Int(PURCHASE_FEES), Global.creator_address()),
            function_transfer_arc72(Txn.sender())
        ),
        Approve()
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete("sale,cancel,200/72")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("fund")), on_fund("sale,create,200/72")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("update_price")), on_update("sale,update,200/72")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("pre_validate")), Approve()],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("buy")), on_buy],
        [
            Or(
                Txn.on_completion() == OnComplete.OptIn,
                Txn.on_completion() == OnComplete.CloseOut,
                Txn.on_completion() == OnComplete.UpdateApplication,
            ),
            Reject(),
        ],
    )

    return program
