from subroutine import *
from main_asa.note_signature import note_signature

note_type = "sale"


def contract_sale_main_asa(proxy_app_id):

    on_create = Seq(
        init_asa(0),
        initialisation_sale(1),
        initialisation_smartcontract(2, proxy_app_id)
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
            function_send_note(Int(ZERO_FEES), Bytes(f"{note_type},buy,{note_signature}")),
            function_contract_fees(App.globalGet(price)),
            function_payment_manager(App.globalGet(price), function_payment),
            function_send_nft_asa(Txn.sender(), Int(1)),
            function_asa_optout(App.globalGet(asa_id)),
            function_close_app(),
            Approve()
        ),
        Reject()
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.DeleteApplication, Seq(function_asa_optout(App.globalGet(asa_id)), on_delete(f"{note_type},cancel,{note_signature}"))],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("fund")), on_fund_optin(f"{note_type},create,{note_signature}")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("update_price")), on_update(f"{note_type},update,{note_signature}")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("pre_validate")), Approve()],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("buy")), on_buy],
        completion_reject()
    )

    return program
