from subroutine import *
from asa_asa.note_signature import note_signature

note_type = "sale"


def contract_sale_asa_asa(proxy_app_id):

    on_create = Seq(
        init_asa(0),
        initialisation_sale(1),
        init_payment_asa(2),
        initialisation_smartcontract(3, proxy_app_id)
    )

    number_asa_hold = AssetHolding.balance(Global.current_application_address(), App.globalGet(asa_id))
    number_asa_buy = ScratchVar(TealType.uint64)
    on_buy = Seq(
        number_asa_hold,
        number_asa_buy.store(Gtxn[Txn.group_index() - Int(1)].asset_amount() / App.globalGet(price)),
        Assert(
            And(
                number_asa_hold.hasValue(),
                number_asa_hold.value() >= number_asa_buy.load(),
                Gtxn[Txn.group_index() - Int(1)].asset_amount() == Mul((number_asa_buy.load()), App.globalGet(price)),
                Gtxn[Txn.group_index() - Int(1)].asset_receiver() == Global.current_application_address(),
                Gtxn[Txn.group_index() - Int(1)].type_enum() == TxnType.AssetTransfer,
                Gtxn[Txn.group_index() - Int(1)].sender() == Txn.sender(),
                Gtxn[Txn.group_index() - Int(1)].xfer_asset() == App.globalGet(paiment_asa_id)
            )
        ),
        function_send_note(Int(ZERO_FEES), Bytes(f"{note_type},buy,{note_signature}")),
        function_contract_fees_asa(Mul((number_asa_buy.load()), App.globalGet(price))),
        function_payment_manager(Mul((number_asa_buy.load()), App.globalGet(price)), function_payment_asa),
        If(number_asa_buy.load() == number_asa_hold.value()).Then(
            function_asa_optout(App.globalGet(paiment_asa_id))
        ),
        end_asa(Txn.sender(), number_asa_buy.load(), number_asa_buy.load() == number_asa_hold.value()),
        Approve()
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.DeleteApplication, Seq(function_asa_optout(App.globalGet(asa_id)), function_asa_optout(App.globalGet(paiment_asa_id)), on_delete(f"{note_type},cancel,{note_signature}"))],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("fund")), on_fund_optin_asa(f"{note_type},create,{note_signature}")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("update_price")), on_update(f"{note_type},update,{note_signature}")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("pre_validate")), Approve()],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("buy")), on_buy],
        completion_reject()
    )

    return program
