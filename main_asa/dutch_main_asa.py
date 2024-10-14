from subroutine import *
from main_asa.note_signature import note_signature

note_type = "dutch"


def contract_dutch_main_asa(proxy_app_id):

    on_create = Seq(
        init_asa(0),
        initialisation_dutch(1),
        initialisation_smartcontract(4, proxy_app_id)
    )

    on_buy = Seq(
        assert_ducth(Gtxn[Txn.group_index() - Int(1)].amount()),
        function_send_note(Int(ZERO_FEES), Bytes(f"{note_type},buy,{note_signature}")),
        function_contract_fees(Gtxn[Txn.group_index() - Int(1)].amount()),
        function_payment_manager(Gtxn[Txn.group_index() - Int(1)].amount(), function_payment),
        end_asa(Txn.sender()),
        Approve()
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.DeleteApplication, Seq(function_asa_optout(App.globalGet(asa_id)), on_delete(f"{note_type},cancel,{note_signature}"))],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("fund")), on_fund_optin(f"{note_type},create,{note_signature}")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("pre_validate")), Approve()],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("buy")), on_buy],
        completion_reject()
    )

    return program
