from pyteal import *
from all_contrat.constants import FEES_ADDRESS, PURCHASE_FEES
from all_contrat.subroutine import fees_address, price, arc200_app_id, arc200_app_address, name, description
from all_contrat.subroutine import function_send_note, function_fund_arc200, function_transfer_arc200
from all_contrat.subroutine import on_fund, on_delete, on_update


def approval_program():

    on_create = Seq(
        App.globalPut(price, Btoi(Txn.application_args[0])),
        App.globalPut(name, Txn.application_args[1]),
        App.globalPut(description, Txn.application_args[2]),
        App.globalPut(arc200_app_id, Btoi(Txn.application_args[3])),
        App.globalPut(arc200_app_address, Txn.application_args[4]),
        App.globalPut(fees_address, Addr(FEES_ADDRESS)),
        Approve(),
    )

    on_buy = Seq(
        Seq(
            function_fund_arc200(),
            function_transfer_arc200(App.globalGet(price)-Int(PURCHASE_FEES), Global.creator_address()),
            function_send_note(Int(PURCHASE_FEES), Bytes("sale,buy,200/rwa")),
        ),
        Approve()
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete("sale,cancel,200/rwa")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("fund")), on_fund("sale,create,200/rwa")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("update_price")), on_update("sale,update,200/rwa")],
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
