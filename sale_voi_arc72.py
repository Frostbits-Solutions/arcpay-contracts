from pyteal import *
from all_contrat.constants import FEES_ADDRESS, PURCHASE_FEES
from all_contrat.subroutine import function_send_note, function_close_app, function_transfer_arc72, function_payment
from all_contrat.subroutine import fees_address, nft_id, nft_app_id, price
from all_contrat.subroutine import on_delete, on_fund, on_update


def approval_program():

    on_create = Seq(
        App.globalPut(nft_app_id, Btoi(Txn.application_args[0])),
        App.globalPut(nft_id, Txn.application_args[1]),
        App.globalPut(price, Btoi(Txn.application_args[2])),
        App.globalPut(fees_address, Addr(FEES_ADDRESS)),
        Approve()
    )

    on_buy = Seq(
        Assert(
            And(
                Gtxn[Txn.group_index() - Int(1)].amount() == App.globalGet(price),
                Gtxn[Txn.group_index() - Int(1)].receiver() == Global.current_application_address(),
                Gtxn[Txn.group_index() - Int(1)].type_enum() == TxnType.Payment,
                Gtxn[Txn.group_index() - Int(1)].sender() == Txn.sender()
            )
        ),
        Seq(
            function_send_note(Int(PURCHASE_FEES), Bytes("sale,buy,1/72")),
            function_payment(App.globalGet(price)-Int(PURCHASE_FEES)),
            function_transfer_arc72(Txn.sender()),
            function_close_app(),
            Approve()
        ),
        Reject()
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete("sale,cancel,1/72")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("fund")), on_fund("sale,create,1/72")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("update_price")), on_update("sale,update,1/72")],
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
