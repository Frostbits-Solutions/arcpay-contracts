from pyteal import *

asa_asa_note_signature = "asa/asa"
fees_address = Bytes('fees_address')
nft_app_id = Bytes("nft_app_id")
nft_id = Bytes("nft_id")
asa_id = Bytes("asa_id")
arc200_app_address = Bytes("arc200_app_address")
arc200_app_id = Bytes("arc200_app_id")
price = Bytes("price")
name = Bytes("name")
description = Bytes("description")
nft_max_price = Bytes("max_price")
nft_min_price = Bytes("min_price")
start_time_key = Bytes("start")
end_time_key = Bytes("end")
late_bid_delay = Bytes("late_bid_delay")
bid_account = Bytes("bid_account")
bid_amount = Bytes("bid_amount")
main_fees = Bytes("main_fees")
fees_app_id = Bytes("fees_app_id")
counter_party_address = Bytes("counter_party_address")
total_client = Bytes('total_client')
paiment_asa_id = Bytes('paiment_asa_id')
nft_app_address = Bytes('nft_app_address')
stock = Bytes('stock')
note_create = Bytes('note_create')
note_update = Bytes('note_update')
note_cancel = Bytes('note_cancel')
note_buy = Bytes('note_buy')
sales_type = Bytes('sales_type')
contract_type = Bytes('contract_type')


def contract_sale(proxy_app_id):
    @Subroutine(TealType.none)
    def function_contract_fees_asa(amount: Expr) -> Expr:
        return Seq(
            read_fees := App.globalGetEx(App.globalGet(fees_app_id), App.globalGet(counter_party_address)),
            read_main_fees := App.globalGetEx(App.globalGet(fees_app_id), main_fees),
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.AssetTransfer,
                    TxnField.xfer_asset: App.globalGet(paiment_asa_id),
                    TxnField.asset_receiver: App.globalGet(fees_address),
                    TxnField.asset_amount: Div(
                        Mul(
                            amount,
                            Add(
                                read_main_fees.value(),
                                read_fees.value()
                            )
                        ),
                        Int(100)
                    ),
                    TxnField.fee: Global.min_txn_fee()
                }
            ),
            InnerTxnBuilder.Next(),
            InnerTxnBuilder.SetFields({
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.application_id: App.globalGet(fees_app_id),
                TxnField.on_completion: OnComplete.NoOp,
                TxnField.application_args: [
                    Bytes("manage_asa_fees"),
                    App.globalGet(counter_party_address),
                    Itob(
                        Div(
                            Mul(
                                amount,
                                read_fees.value()
                            ),
                            Int(100)
                        )
                    )
                ]
            }),
            InnerTxnBuilder.Submit(),
        )

    @Subroutine(TealType.none)
    def function_contract_fees(amount: Expr) -> Expr:
        return Seq(
            read_fees := App.globalGetEx(App.globalGet(fees_app_id), App.globalGet(counter_party_address)),
            read_main_fees := App.globalGetEx(App.globalGet(fees_app_id), main_fees),
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.Payment,
                    TxnField.amount: Div(
                        Mul(
                            amount,
                            Add(
                                read_main_fees.value(),
                                read_fees.value()
                            )
                        ),
                        Int(100)
                    ),
                    TxnField.sender: Global.current_application_address(),
                    TxnField.receiver: App.globalGet(fees_address)
                }
            ),
            InnerTxnBuilder.Next(),
            InnerTxnBuilder.SetFields({
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.application_id: App.globalGet(fees_app_id),
                TxnField.on_completion: OnComplete.NoOp,
                TxnField.application_args: [
                    Bytes("manage_network_fees"),
                    App.globalGet(counter_party_address),
                    Itob(
                        Div(
                            Mul(
                                amount,
                                read_fees.value()
                            ),
                            Int(100)
                        )
                    )
                ]
            }),
            InnerTxnBuilder.Submit(),
        )

    @Subroutine(TealType.none)
    def function_close_app() -> Expr:
        return Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.Payment,
                    TxnField.close_remainder_to: Global.creator_address(),
                }
            ),
            InnerTxnBuilder.Submit()
        )

    def function_payment_manager(amount: Expr, main_function) -> Expr:
        return Seq(
            read_fees := App.globalGetEx(App.globalGet(fees_app_id), App.globalGet(counter_party_address)),
            read_main_fees := App.globalGetEx(App.globalGet(fees_app_id), main_fees),
            main_function(
                Minus(
                    amount,
                    Div(
                        Mul(
                            amount,
                            Add(
                                read_main_fees.value(),
                                read_fees.value()
                            )
                        ),
                        Int(100)
                    )
                ),
                Global.creator_address(),
                Bytes('')
            )
        )

    @Subroutine(TealType.none)
    def function_payment_asa(amount: Expr, to: Expr, note: Expr) -> Expr:
        return function_send_asa(amount, to, App.globalGet(paiment_asa_id), note)

    @Subroutine(TealType.none)
    def function_send_asa(amount: Expr, to: Expr, asset_id: Expr, note: Expr) -> Expr:
        return Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.AssetTransfer,
                    TxnField.xfer_asset: asset_id,
                    TxnField.asset_receiver: to,
                    TxnField.asset_amount: amount,
                    TxnField.fee: Global.min_txn_fee(),
                    TxnField.note: note
                }
            ),
            InnerTxnBuilder.Submit()
        )

    @Subroutine(TealType.none)
    def function_send_algo(amount: Expr, to: Expr, note) -> Expr:
        return Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.Payment,
                    TxnField.amount: amount,
                    TxnField.sender: Global.current_application_address(),
                    TxnField.receiver: to,
                    TxnField.note: note,
                    TxnField.fee: Global.min_txn_fee()
                }
            ),
            InnerTxnBuilder.Submit()
        )

    @Subroutine(TealType.none)
    def function_asa_optout(asset_id) -> Expr:
        return Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.AssetTransfer,
                    TxnField.xfer_asset: asset_id,
                    TxnField.asset_close_to: Global.creator_address(),
                    TxnField.sender: Global.current_application_address(),
                }
            ),
            InnerTxnBuilder.Submit(),
        )

    @Subroutine(TealType.none)
    def function_asa_opt_in(asset_id) -> Expr:
        return Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.AssetTransfer,
                    TxnField.xfer_asset: App.globalGet(asset_id),
                    TxnField.asset_receiver: Global.current_application_address(),
                }
            ),
            InnerTxnBuilder.Submit()
        )

    on_fund_selection = Seq(
        # Check the sender is the creator
        Assert(Txn.sender() == Global.creator_address()),
        # Set-up all the variables
        App.globalPut(paiment_asa_id, Btoi(Txn.application_args[1])),
        App.globalPut(asa_id, Btoi(Txn.application_args[2])),
        App.globalPut(price, Btoi(Txn.application_args[3])),
        App.globalPut(counter_party_address, Txn.sender()),
        App.globalPut(fees_app_id, Int(proxy_app_id)),
        App.globalPut(fees_address, Sha512_256(Concat(Bytes("appID"), Itob(App.globalGet(fees_app_id))))),
        App.globalPut(sales_type, Bytes('sale')),
        If(
            Btoi(Txn.application_args[0]) == Int(1)
        ).Then(
            App.globalPut(contract_type, Bytes('1/asa')),
        ).Else(
            App.globalPut(contract_type, Bytes('asa/asa')),
        ),
        App.globalPut(note_create, Concat(App.globalGet(sales_type), Bytes(',create,'), App.globalGet(contract_type))),
        App.globalPut(note_update, Concat(App.globalGet(sales_type), Bytes(',update,'), App.globalGet(contract_type))),
        App.globalPut(note_cancel, Concat(App.globalGet(sales_type), Bytes(',cancel,'), App.globalGet(contract_type))),
        App.globalPut(note_buy, Concat(App.globalGet(sales_type), Bytes(',buy,'), App.globalGet(contract_type))),

        # Get the creation fees and send them to the proxy-contract
        creation_fees := App.globalGetEx(
            App.globalGet(fees_app_id),
            Concat(Bytes('creation_'), App.globalGet(counter_party_address))
        ),
        main_creation_fees := App.globalGetEx(
            App.globalGet(fees_app_id),
            Bytes('main_fees_creation')
        ),
        If(
            creation_fees.value() == Int(0)
        ).Then(
            # function_send_algo(main_creation_fees.value(), App.globalGet(fees_address), App.globalGet(note_create)),
            function_send_algo(Int(0), App.globalGet(fees_address), App.globalGet(note_create)),
        ).Else(
            # function_send_algo(creation_fees.value(), App.globalGet(fees_address), App.globalGet(note_create)),
            function_send_algo(Int(0), App.globalGet(fees_address), App.globalGet(note_create)),
        ),

        # Opt-in the asa_id
        function_asa_opt_in(asa_id),
        # If paiment is not Algo, opt-in the paiment_asa_id
        If(
            App.globalGet(paiment_asa_id) != Int(1)
        ).Then(
            function_asa_opt_in(paiment_asa_id)
        ),
        Approve()
    )

    on_update = Seq(
        Assert(
            And(
                Txn.sender() == Global.creator_address(),
                Btoi(Txn.application_args[1]) > Int(0)
            )
        ),
        function_send_algo(Int(0), App.globalGet(fees_address), App.globalGet(note_update)),
        App.globalPut(price, Btoi(Txn.application_args[1])),
        Approve()
    )

    on_delete_selection = Seq(
        Assert(Txn.sender() == Global.creator_address()),
        If(
            Balance(Global.current_application_address()) != Int(0)
        ).Then(
            function_asa_optout(App.globalGet(asa_id)),
            If(
                App.globalGet(paiment_asa_id) != Int(1)
            ).Then(
                function_asa_optout(App.globalGet(paiment_asa_id)),
            ),
            function_send_algo(Int(0), App.globalGet(fees_address), App.globalGet(note_cancel)),
            function_close_app(),
        ),
        Approve()
    )

    number_asa_hold = AssetHolding.balance(Global.current_application_address(), App.globalGet(asa_id))
    number_asa_buy = ScratchVar(TealType.uint64)
    on_buy = Seq(
        number_asa_hold,
        If(
            App.globalGet(paiment_asa_id) == Int(1)
        ).Then(
            number_asa_buy.store(Gtxn[Txn.group_index() - Int(1)].amount() / App.globalGet(price)),
            Assert(
                And(
                    number_asa_hold.hasValue(),
                    number_asa_hold.value() >= number_asa_buy.load(),
                    Gtxn[Txn.group_index() - Int(1)].sender() == Txn.sender(),
                    Gtxn[Txn.group_index() - Int(1)].amount() == Mul((number_asa_buy.load()), App.globalGet(price)),
                    Gtxn[Txn.group_index() - Int(1)].receiver() == Global.current_application_address(),
                    Gtxn[Txn.group_index() - Int(1)].type_enum() == TxnType.Payment,
                )
            ),
            function_send_algo(Int(0), App.globalGet(fees_address), App.globalGet(note_buy)),
            function_contract_fees(Mul(number_asa_buy.load(), App.globalGet(price))),
            function_payment_manager(Mul(number_asa_buy.load(), App.globalGet(price)), function_send_algo),
            function_send_asa(number_asa_buy.load(), Txn.sender(), App.globalGet(asa_id), Bytes("")),
            If(number_asa_buy.load() == number_asa_hold.value()).Then(
                function_asa_optout(App.globalGet(asa_id)),
                function_close_app()
            ),
        ).Else(
            number_asa_buy.store(Gtxn[Txn.group_index() - Int(1)].asset_amount() / App.globalGet(price)),
            Assert(
                And(
                    number_asa_hold.hasValue(),
                    number_asa_hold.value() >= number_asa_buy.load(),
                    Gtxn[Txn.group_index() - Int(1)].sender() == Txn.sender(),
                    Gtxn[Txn.group_index() - Int(1)].asset_amount() == Mul((number_asa_buy.load()), App.globalGet(price)),
                    Gtxn[Txn.group_index() - Int(1)].asset_receiver() == Global.current_application_address(),
                    Gtxn[Txn.group_index() - Int(1)].type_enum() == TxnType.AssetTransfer,
                    Gtxn[Txn.group_index() - Int(1)].xfer_asset() == App.globalGet(paiment_asa_id)
                )
            ),
            function_send_algo(Int(0), App.globalGet(fees_address), App.globalGet(note_buy)),
            function_contract_fees_asa(Mul((number_asa_buy.load()), App.globalGet(price))),
            function_payment_manager(Mul((number_asa_buy.load()), App.globalGet(price)), function_payment_asa),
            function_send_asa(number_asa_buy.load(), Txn.sender(), App.globalGet(asa_id), Bytes("")),
            If(number_asa_buy.load() == number_asa_hold.value()).Then(
                function_asa_optout(App.globalGet(asa_id)),
                function_asa_optout(App.globalGet(paiment_asa_id)),
                function_close_app(),
            ),
        ),
        Approve()
    )

    program = Cond(
        [Txn.application_id() == Int(0), Approve()],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete_selection],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("pre_validate")), Approve()],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("fund")), on_fund_selection],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("update_price")), on_update],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("buy")), on_buy],
        [
            Or(
                Txn.on_completion() == OnComplete.OptIn,
                Txn.on_completion() == OnComplete.CloseOut,
                Txn.on_completion() == OnComplete.UpdateApplication
            ),
            Reject()
        ]
    )

    return program


ALGO = False
from algosdk import transaction, mnemonic, account
from tools import compile_program, clear_state_program, wait_for_confirmation, get_application_address
from algosdk.v2client.algod import AlgodClient

client = AlgodClient(
    algod_token="",
    algod_address="https://testnet-api.algonode.cloud",
    headers={"X-Algo-API-Token": ""},
)
mnemonic_creator = "arrest pear require glad middle legend army stick bounce brush oyster police family version width endorse inquiry expand voice knee where foam search absent flush"
private_key_creator = mnemonic.to_private_key(mnemonic_creator)
public_key_creator = account.address_from_private_key(private_key_creator)
print(public_key_creator)

txn = transaction.ApplicationCreateTxn(
    sender=public_key_creator,
    on_complete=transaction.OnComplete.NoOpOC,
    approval_program=compile_program(contract_sale(733560801)),
    clear_program=compile_program(clear_state_program()),
    global_schema=transaction.StateSchema(num_uints=8, num_byte_slices=8),
    local_schema=transaction.StateSchema(num_uints=0, num_byte_slices=0),
    sp=client.suggested_params(),
)
signed_txn = txn.sign(private_key_creator)
sended_txn = client.send_transaction(signed_txn)
result = wait_for_confirmation(client, sended_txn)
app_id = result['application-index']
app_address = get_application_address(app_id)
print("Creation app id:", app_id)
print("Application Address", app_address)

if ALGO:
    input("fund")
    try:
        sp=client.suggested_params()
        pay_tx = transaction.PaymentTxn(
            sender=public_key_creator,
            sp=sp,
            receiver=app_address,
            amt=2000000

        )

        txn = transaction.ApplicationCallTxn(
            sender=public_key_creator,
            sp=sp,
            index=app_id,
            foreign_apps=[733560801],
            foreign_assets=[718663983],
            on_complete=transaction.OnComplete.NoOpOC,
            app_args=[b"fund", 1, 718663983, 100_000]
        )
        transaction.assign_group_id([
            pay_tx, txn
        ])

        signed_pay = pay_tx.sign(private_key_creator)
        signed_txn = txn.sign(private_key_creator)
        sended_txn = client.send_transactions([signed_pay, signed_txn])
        result = wait_for_confirmation(client, sended_txn)
        print(result)
    except Exception as e:
        print("error", e)

    input("update")
    try:
        sp=client.suggested_params()
        txn = transaction.ApplicationCallTxn(
            sender=public_key_creator,
            sp=sp,
            index=app_id,
            accounts=['EAG7SE6UPLOU3BOCYYLFLQ7QPZHDZ52D5EWFM77WFEIYKALINETOOFIUSU'],
            on_complete=transaction.OnComplete.NoOpOC,
            app_args=[b"update_price", 1]
        )
        signed_txn = txn.sign(private_key_creator)
        sended_txn = client.send_transactions([signed_txn])
        result = wait_for_confirmation(client, sended_txn)
        print(result)
    except Exception as e:
        print("error", e)

    input("delete")
    txn = transaction.ApplicationDeleteTxn(
        sender=public_key_creator,

        sp=client.suggested_params(),
        index=app_id,
        foreign_assets=[718663983],
        accounts=['EAG7SE6UPLOU3BOCYYLFLQ7QPZHDZ52D5EWFM77WFEIYKALINETOOFIUSU']

    )
    signed_txn = txn.sign(private_key_creator)
    sended_txn = client.send_transaction(signed_txn)
    result = wait_for_confirmation(client, sended_txn)
    print(result)
else:
    input("fund")
    try:
        sp = client.suggested_params()
        pay_tx = transaction.PaymentTxn(
            sender=public_key_creator,
            sp=sp,
            receiver=app_address,
            amt=2000000

        )

        txn = transaction.ApplicationCallTxn(
            sender=public_key_creator,
            sp=sp,
            index=app_id,
            foreign_apps=[733560801],
            foreign_assets=[718663983, 10458941],
            on_complete=transaction.OnComplete.NoOpOC,
            app_args=[b"fund", 10458941, 718663983, 100_000]
        )
        transaction.assign_group_id([
            pay_tx, txn
        ])

        signed_pay = pay_tx.sign(private_key_creator)
        signed_txn = txn.sign(private_key_creator)
        sended_txn = client.send_transactions([signed_pay, signed_txn])
        result = wait_for_confirmation(client, sended_txn)
        print(result)
    except Exception as e:
        print("error", e)

    input("update")
    try:
        sp = client.suggested_params()
        txn = transaction.ApplicationCallTxn(
            sender=public_key_creator,
            sp=sp,
            index=app_id,
            accounts=['EAG7SE6UPLOU3BOCYYLFLQ7QPZHDZ52D5EWFM77WFEIYKALINETOOFIUSU'],
            on_complete=transaction.OnComplete.NoOpOC,
            app_args=[b"update_price", 1]
        )
        signed_txn = txn.sign(private_key_creator)
        sended_txn = client.send_transactions([signed_txn])
        result = wait_for_confirmation(client, sended_txn)
        print(result)
    except Exception as e:
        print("error", e)

    input("delete")
    txn = transaction.ApplicationDeleteTxn(
        sender=public_key_creator,

        sp=client.suggested_params(),
        index=app_id,
        foreign_assets=[718663983, 10458941],
        accounts=['EAG7SE6UPLOU3BOCYYLFLQ7QPZHDZ52D5EWFM77WFEIYKALINETOOFIUSU']

    )
    signed_txn = txn.sign(private_key_creator)
    sended_txn = client.send_transaction(signed_txn)
    result = wait_for_confirmation(client, sended_txn)
    print(result)