from pyteal import *

# CONFIG
CREATE_FEES = 0
ZERO_FEES = 0
# voi 87414541
# algo 718742597
FEES_APP_ID = 87414541


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
def function_fund_arc(arc_app_address) -> Expr:
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.amount: Int(28500),
                TxnField.sender: Global.current_application_address(),
                TxnField.receiver: App.globalGet(arc_app_address)
            }
        ),
        InnerTxnBuilder.Submit(),
    )


@Subroutine(TealType.bytes)
def app_addr_from_id(app_id):
    return Sha512_256(
        Concat(Bytes("appID"), Itob(app_id))
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
                Bytes("manage_network_fees"),
                App.globalGet(counter_party_address),
                Itob(amount_counter_party)
            ]
        }),
        InnerTxnBuilder.Submit(),
    )


@Subroutine(TealType.none)
def function_contract_fees_asa(amount: Expr, amount_counter_party: Expr) -> Expr:
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.xfer_asset: App.globalGet(paiment_asa_id),
                TxnField.asset_receiver: App.globalGet(fees_address),
                TxnField.asset_amount: amount,
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
                Bytes("manage_arc200_fees"),
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
            function_send_note(Int(ZERO_FEES), Bytes(note)),
            App.globalPut(price, Btoi(Txn.application_args[1])),
            Approve()
        ),
        Reject()
    )


def on_delete(note):
    return Seq(
        Assert(Txn.sender() == Global.creator_address()),
        function_send_note(Int(ZERO_FEES), Bytes(note)),
        function_close_app(),
        Approve()
    )


def on_fund(note):
    return Seq(
        Assert(Txn.sender() == Global.creator_address()),
        function_send_note(Int(CREATE_FEES), Bytes(note)),
        Approve()
    )


def on_fund_optin_only_asa(note):
    return Seq(
        Assert(Txn.sender() == Global.creator_address()),
        function_send_note(Int(CREATE_FEES), Bytes(note)),
        Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.AssetTransfer,
                    TxnField.xfer_asset: App.globalGet(paiment_asa_id),
                    TxnField.asset_receiver: Global.current_application_address(),
                }
            ),
            InnerTxnBuilder.Submit()
        ),
        Approve()
    )


def on_fund_optin_asa(note):
    return Seq(
        Assert(Txn.sender() == Global.creator_address()),
        function_send_note(Int(CREATE_FEES), Bytes(note)),
        Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.AssetTransfer,
                    TxnField.xfer_asset: App.globalGet(asa_id),
                    TxnField.asset_receiver: Global.current_application_address(),
                }
            ),
            InnerTxnBuilder.Submit()
        ),
        Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.AssetTransfer,
                    TxnField.xfer_asset: App.globalGet(paiment_asa_id),
                    TxnField.asset_receiver: Global.current_application_address(),
                }
            ),
            InnerTxnBuilder.Submit()
        ),
        Approve()
    )

def on_fund_optin(note):
    return Seq(
        Assert(Txn.sender() == Global.creator_address()),
        function_send_note(Int(CREATE_FEES), Bytes(note)),
        Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.AssetTransfer,
                    TxnField.xfer_asset: App.globalGet(asa_id),
                    TxnField.asset_receiver: Global.current_application_address(),
                }
            ),
            InnerTxnBuilder.Submit()
        ),
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


@Subroutine(TealType.none)
def function_send_nft_asa(account: Expr, amount: Expr) -> Expr:
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.xfer_asset: App.globalGet(asa_id),
                TxnField.asset_receiver: account,
                TxnField.asset_amount: amount,
                TxnField.fee: Global.min_txn_fee()
            }
        ),
        InnerTxnBuilder.Submit()
    )


@Subroutine(TealType.none)
def function_payment_asa(amount: Expr) -> Expr:
    return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.xfer_asset: App.globalGet(paiment_asa_id),
                TxnField.asset_receiver: Global.creator_address(),
                TxnField.asset_amount: amount,
                TxnField.fee: Global.min_txn_fee()
            }
        ),
        InnerTxnBuilder.Submit(),
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


def initialisation_smartcontract(index):
    return Seq(
        App.globalPut(counter_party_address, Txn.application_args[index]),
        App.globalPut(fees_app_id, Int(FEES_APP_ID)),
        App.globalPut(fees_address, app_addr_from_id(App.globalGet(fees_app_id))),
        App.globalPut(main_fees, Int(2)),
        Approve(),
    )


def initialisation_auction():
    return Seq(
        App.globalPut(bid_account, Global.zero_address()),
        App.globalPut(late_bid_delay, Int(600)),
        App.globalPut(bid_amount, Int(0)),
    )


def initialisation_dutch():
    return Seq(
        App.globalPut(start_time_key, Global.latest_timestamp()),
        Assert(App.globalGet(nft_max_price) > App.globalGet(nft_min_price)),
        Assert(App.globalGet(end_time_key) > App.globalGet(start_time_key)),
    )


def initialisation_rwa():
    return Seq(
        App.globalPut(price, Btoi(Txn.application_args[0])),
        App.globalPut(name, Txn.application_args[1]),
        App.globalPut(description, Txn.application_args[2]),
    )


def initialisation_arc72():
    return Seq(
        App.globalPut(nft_app_id, Btoi(Txn.application_args[0])),
        App.globalPut(nft_id, Txn.application_args[1]),
        App.globalPut(nft_app_address, app_addr_from_id(App.globalGet(nft_app_id))),
    )
