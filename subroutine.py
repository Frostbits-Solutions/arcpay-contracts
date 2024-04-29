from pyteal import *


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
                TxnField.receiver: App.globalGet(fees_address),
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
