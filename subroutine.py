from pyteal import *


NOTE_ADDRESS = '3FXLFER4JF4SPVBSSTPZWGTFUYSD54QOEZ4Y4TV4ZTRHERT2Z6DH7Q54YQ'
FEES_ADDRESS = 'JTVFVVZ62GAKYZIS6GCQJMQZXX2UXAAPIOP4GYLMEF3J4UT5FWWVLXMP4E'#'HYGWVRG7UKZWMGIGV2HCGDQDQ4Q5CDZZVTSB4L6BE4PZQX4QTHPPNTZU7A'
FEES_APP_ID = 49621948#49547082
ZERO_FEES = 0
PURCHASE_FEES = 0

fees_address = Bytes('fees_address')
nft_app_id = Bytes("nft_app_id")
nft_id = Bytes("nft_id")
arc200_app_address = Bytes("arc200_app_address")
arc200_app_id = Bytes("arc200_app_id")
price = Bytes("price")
CREATE_FEES = 0
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
counter_party_fees = Bytes("counter_party_fees")
fees_app_id = Bytes("fees_app_id")
counter_party_address = Bytes("counter_party_address")
note_address = Bytes('note_address')


@Subroutine(TealType.none)
def function_close_app() -> Expr:
    return If(
        Balance(Global.current_application_address()) != Int(0)
    ).Then(
        Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.Payment,
                    TxnField.close_remainder_to: Global.creator_address(),
                }
            ),
            InnerTxnBuilder.Submit()
        )
    )


@Subroutine(TealType.none)
def function_fund_arc200() -> Expr:
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.amount: Int(28500),
                TxnField.sender: Global.current_application_address(),
                TxnField.receiver: App.globalGet(arc200_app_address)
            }
        ),
        InnerTxnBuilder.Submit(),
    )


@Subroutine(TealType.none)
def function_send_note(amount: Expr, note: Expr) -> Expr:
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.amount: amount,
                TxnField.sender: Global.current_application_address(),
                TxnField.receiver: App.globalGet(note_address),
                TxnField.note: note
            }
        ),
        InnerTxnBuilder.Submit()
    )


@Subroutine(TealType.none)
def function_transfer_arc200(amount: Expr, to: Expr) -> Expr:
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.application_id: App.globalGet(arc200_app_id),
                TxnField.on_completion: OnComplete.NoOp,
                TxnField.application_args: [
                    Bytes("base16", "da7025b9"),
                    to,
                    Concat(BytesZero(Int(24)), Itob(amount))
                ]
            }
        ),
        InnerTxnBuilder.Submit(),
    )


@Subroutine(TealType.none)
def function_payment(amount: Expr) -> Expr:
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.amount: amount,
                TxnField.sender: Global.current_application_address(),
                TxnField.receiver: Global.creator_address()
            }
        ),
        InnerTxnBuilder.Submit()
    )


@Subroutine(TealType.none)
def function_contract_fees(amount: Expr, amount_counter_party: Expr) -> Expr:
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.amount: amount,
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
                Bytes("add_network_fees"),
                App.globalGet(counter_party_address),
                Itob(amount_counter_party)
            ]
        }),
        InnerTxnBuilder.Submit(),
    )


@Subroutine(TealType.none)
def function_contract_fees_arc200(amount: Expr, amount_counter_party: Expr) -> Expr:
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.ApplicationCall,
                TxnField.application_id: App.globalGet(arc200_app_id),
                TxnField.on_completion: OnComplete.NoOp,
                TxnField.application_args: [
                    Bytes("base16", "da7025b9"),
                    App.globalGet(fees_address),
                    Concat(BytesZero(Int(24)), Itob(amount))
                ]
            }
        ),
        InnerTxnBuilder.Next(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.ApplicationCall,
            TxnField.application_id: App.globalGet(fees_app_id),
            TxnField.on_completion: OnComplete.NoOp,
            TxnField.application_args: [
                Bytes("add_arc200_fees"),
                App.globalGet(counter_party_address),
                Itob(amount_counter_party),
                Itob(App.globalGet(arc200_app_id)),
            ]
        }),
        InnerTxnBuilder.Submit(),
    )


@Subroutine(TealType.none)
def function_transfer_arc72(to: Expr) -> Expr:
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.ApplicationCall,
            TxnField.application_id: App.globalGet(nft_app_id),
            TxnField.on_completion: OnComplete.NoOp,
            TxnField.application_args: [
                Bytes("base16", "f2f194a0"),
                Global.creator_address(),
                to,
                App.globalGet(nft_id)
            ]
        }),
        InnerTxnBuilder.Submit(),
    )


def on_update(note):
    return Seq(
        Assert(
            And(
                Txn.sender() == Global.creator_address(),
                Btoi(Txn.application_args[1]) > Int(0)
            )
        ),
        Seq(
            function_send_note(Int(0), Bytes(note)),
            App.globalPut(price, Btoi(Txn.application_args[1])),
            Approve()
        ),
        Reject()
    )


def on_delete(note):
    return Seq(
        function_send_note(Int(0), Bytes(note)),
        Assert(Txn.sender() == Global.creator_address()),
        function_close_app(),
        Approve()
    )


def on_fund(note):
    return Seq(
        Assert(Txn.sender() == Global.creator_address()),
        function_send_note(Int(CREATE_FEES), Bytes(note)),
        Approve()
    )


def completion_reject():
    return [
        Or(
            Txn.on_completion() == OnComplete.OptIn,
            Txn.on_completion() == OnComplete.CloseOut,
            Txn.on_completion() == OnComplete.UpdateApplication
        ),
        Reject()
    ]
