from subroutine import *
from asa_rwa.note_signature import note_signature

note_type = "sale"


def contract_sale_asa_rwa(proxy_app_id):

    on_create = Seq(
        initialisation_sale(0),
        initialisation_rwa(1),
        init_payment_asa(3),
        initialisation_smartcontract(4, proxy_app_id)
    )

    on_buy = Seq(
        Assert(
            And(
                Gtxn[Txn.group_index() - Int(1)].asset_amount() == App.globalGet(price),
                Gtxn[Txn.group_index() - Int(1)].asset_receiver() == Global.current_application_address(),
                Gtxn[Txn.group_index() - Int(1)].type_enum() == TxnType.AssetTransfer,
                Gtxn[Txn.group_index() - Int(1)].sender() == Txn.sender(),
                Gtxn[Txn.group_index() - Int(1)].xfer_asset() == App.globalGet(paiment_asa_id)
            )
        ),
        function_send_note(Int(ZERO_FEES), Bytes(f"{note_type},buy,{note_signature}")),
        function_contract_fees_asa(App.globalGet(price)),
        function_payment_manager(App.globalGet(price), function_payment_asa),
        function_asa_optout(App.globalGet(paiment_asa_id)),
        function_close_app(),
        Approve()
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.DeleteApplication, Seq(function_asa_optout(App.globalGet(paiment_asa_id)), on_delete(f"{note_type},cancel,{note_signature}"))],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("fund")), on_fund_optin_only_asa(f"{note_type},create,{note_signature}")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("update_price")), on_update(f"{note_type},update,{note_signature}")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("buy")), on_buy],
        completion_reject()
    )

    return program
