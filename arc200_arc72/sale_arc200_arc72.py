from subroutine import *
from arc200_arc72.note_signature import note_signature

note_type = "sale"


def contract_sale_arc200_arc72(proxy_app_id):

    on_create = Seq(
        initialisation_arc72(0),
        initialisation_sale(2),
        initialisation_arc200(3),
        initialisation_smartcontract(4, proxy_app_id)
    )

    on_buy = Seq(
        function_send_note(Int(ZERO_FEES), Bytes(f"{note_type},buy,{note_signature}")),
        function_contract_fees_arc200(App.globalGet(price)),
        function_fund_arc(arc200_app_address),
        function_payment_manager(App.globalGet(price), function_transfer_arc200),
        end_arc72(Txn.sender()),
        Approve()
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete(f"{note_type},cancel,{note_signature}")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("fund")), on_fund(f"{note_type},create,{note_signature}")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("update_price")), on_update(f"{note_type},update,{note_signature}")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("pre_validate")), Approve()],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("buy")), on_buy],
        completion_reject()
    )

    return program
