from pyteal import *


def approval_program():

    # ################################################################################################################ #
    # #############################################                      ############################################# #
    # ############################################# Create Fees Contract ############################################# #
    # #############################################                      ############################################# #
    # ################################################################################################################ #

    on_create = Seq(
        App.globalPut(Concat(Bytes('m_'), Txn.sender()), Txn.sender()),
        App.globalPut(Bytes('main_fees'), Int(2)),
        Approve()
    )

    # ################################################################################################################ #
    # ###############################################                  ############################################### #
    # ############################################### Update Main Fees ############################################### #
    # ###############################################                  ############################################### #
    # ################################################################################################################ #

    update_main_fees = Seq(
        Assert(App.globalGet(Concat(Bytes('m_'), Txn.sender())) == Txn.sender()),
        App.globalPut(Bytes('main_fees'), Btoi(Txn.application_args[1])),
    )

    # ################################################################################################################ #
    # ###############################################                  ############################################### #
    # ############################################### Add & Del Master ############################################### #
    # ###############################################                  ############################################### #
    # ################################################################################################################ #

    add_master = Seq(
        Assert(App.globalGet(Concat(Bytes('m_'), Txn.sender())) == Txn.sender()),
        App.globalPut(Concat(Bytes('m_'), Txn.application_args[1]), Txn.application_args[1]),
        Approve()
    )

    del_master = Seq(
        Assert(App.globalGet(Concat(Bytes('m_'), Txn.sender())) == Txn.sender()),
        App.globalDel(Concat(Bytes('m_'), Txn.application_args[1])),
        Approve()
    )

    # ################################################################################################################ #
    # ###############################################                  ############################################### #
    # ############################################### Add & Del Client ############################################### #
    # ###############################################                  ############################################### #
    # ################################################################################################################ #

    add_client = Seq(
        Assert(App.globalGet(Concat(Bytes('m_'), Txn.sender())) == Txn.sender()),
        App.globalPut(Txn.application_args[1], Int(1)),
        Approve()
    )

    del_client = Seq(
        Assert(App.globalGet(Concat(Bytes('m_'), Txn.sender())) == Txn.sender()),
        App.globalDel(Txn.application_args[1]),
        Approve(),
    )

    # ################################################################################################################ #
    # ################################################               ################################################# #
    # ################################################ Add & Del Asa ################################################# #
    # ################################################               ################################################# #
    # ################################################################################################################ #

    add_asa = Seq(
        Assert(App.globalGet(Concat(Bytes('m_'), Txn.sender())) == Txn.sender()),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.xfer_asset: Btoi(Txn.application_args[1]),
                TxnField.asset_receiver: Global.current_application_address(),
            }
        ),
        InnerTxnBuilder.Submit(),
        Approve()
    )

    del_asa = Seq(
        Assert(App.globalGet(Concat(Bytes('m_'), Txn.sender())) == Txn.sender()),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.xfer_asset: Btoi(Txn.application_args[1]),
                TxnField.asset_close_to: Txn.sender()
            }
        ),
        InnerTxnBuilder.Submit(),
        Approve()
    )

    # ################################################################################################################ #
    # ##########################################                            ########################################## #
    # ########################################## Manage fees for the Client ########################################## #
    # ##########################################                            ########################################## #
    # ################################################################################################################ #

    # Manage network fees
    manage_network_fees = Seq(
        If(
            And(
                # Check client has more than 0 as fees
                App.globalGet(Txn.application_args[1]) > Int(0),
                # Check the amount send in tx is greater than the fees to add
                Gtxn[Txn.group_index() - Int(1)].amount() >= Btoi(Txn.application_args[2])
            )

        ).Then(
            # Send the fees
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.Payment,
                    TxnField.amount: Btoi(Txn.application_args[2]),
                    TxnField.sender: Global.current_application_address(),
                    TxnField.receiver: Txn.application_args[1]
                }
            ),
            InnerTxnBuilder.Submit(),
        ),
        Approve()
    )

    # Manage asa fees
    client_holding_asa = AssetHolding.balance(Txn.application_args[1], Gtxn[Txn.group_index() - Int(1)].xfer_asset())
    manage_asa_fees = Seq(
        client_holding_asa,
        If(
            And(
                # Test if the payment is an asset transfer
                Gtxn[Txn.group_index() - Int(1)].type_enum() == TxnType.AssetTransfer,
                # Check the client exist
                App.globalGet(Txn.application_args[1]) > Int(0),
                # Check the amount send in tx is greater than the fees to add
                Gtxn[Txn.group_index() - Int(1)].asset_amount() > Btoi(Txn.application_args[2]),
                # Check the client has opt-in the asa
                client_holding_asa.hasValue()
            )
        ).Then(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.AssetTransfer,
                    TxnField.xfer_asset: Gtxn[Txn.group_index() - Int(1)].xfer_asset(),
                    TxnField.asset_receiver: Txn.application_args[1],
                    TxnField.asset_amount: Btoi(Txn.application_args[2]),
                    TxnField.fee: Global.min_txn_fee()
                }
            ),
            InnerTxnBuilder.Submit()
        ),
        Approve()
    )

    # Manage arc200 fees
    # TODO add check if client as ARC200
    manage_arc200_fees = Seq(
        If(
            And(
                # Check the client exist
                App.globalGet(Txn.application_args[1]) > Int(0),
                # Test if the payment is an application call for an arc200
                Gtxn[Txn.group_index() - Int(1)].type_enum() == TxnType.ApplicationCall,
                Gtxn[Txn.group_index() - Int(1)].application_args[0] == Bytes("base16", "da7025b9"),
                # Test it is sent to our address
                Gtxn[Txn.group_index() - Int(1)].application_args[1] == Global.current_application_address(),
                # # Check the amount send in tx is greater than the fees to add
                Btoi(Extract(Gtxn[Txn.group_index() - Int(1)].application_args[2], Int(24), Int(8))) > Btoi(Txn.application_args[2]),
            )
        ).Then(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.ApplicationCall,
                    TxnField.application_id: Gtxn[Txn.group_index() - Int(1)].application_id(),
                    TxnField.on_completion: OnComplete.NoOp,
                    TxnField.application_args: [
                        Bytes("base16", "da7025b9"),
                        Txn.application_args[1],
                        Concat(BytesZero(Int(24)), Txn.application_args[2])
                    ]
                }
            ),
            InnerTxnBuilder.Submit()
        ),
        Approve()
    )

    # ################################################################################################################ #
    # ################################################                ################################################ #
    # ################################################ Claim our fees ################################################ #
    # ################################################                ################################################ #
    # ################################################################################################################ #

    # Claim network fees
    claim_network_fees = Seq(
        Assert(
            And(
                # Check a master is claiming
                App.globalGet(Concat(Bytes('m_'), Txn.sender())) == Txn.sender(),
                # Check network to send is greater than 0
                Balance(Global.current_application_address()) > Add(Global.min_balance(), Int(100_000))
            )
        ),
        # Send the network fees
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.Payment,
            TxnField.amount: Minus(
                Balance(Global.current_application_address()),
                Add(Global.min_balance(), Int(100_000))
            ),
            TxnField.sender: Global.current_application_address(),
            TxnField.receiver: Txn.sender()
        }),
        InnerTxnBuilder.Submit(),
        Approve()
    )

    # Claim asa fees
    contract_holding_asa = AssetHolding.balance(Global.current_application_address(), Btoi(Txn.application_args[1]))
    claim_asa_fees = Seq(
        contract_holding_asa,
        Assert(App.globalGet(Concat(Bytes('m_'), Txn.sender())) == Txn.sender()),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.xfer_asset: Btoi(Txn.application_args[1]),
                TxnField.asset_receiver: Txn.sender(),
                TxnField.asset_amount: contract_holding_asa.value(),
                TxnField.fee: Global.min_txn_fee()
            }
        ),
        InnerTxnBuilder.Submit(),
        Approve()
    )

    # ################################################################################################################ #
    # ################################################                ################################################ #
    # ################################################ Delete the App ################################################ #
    # ################################################                ################################################ #
    # ################################################################################################################ #

    del_app = Seq(
        Assert(App.globalGet(Concat(Bytes('m_'), Txn.sender())) == Txn.sender()),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.close_remainder_to: Txn.sender()
            }
        ),
        InnerTxnBuilder.Submit(),
        Approve()
    )

    # ################################################################################################################ #
    # #################################################              ################################################# #
    # ################################################# Main Program ################################################# #
    # #################################################              ################################################# #
    # ################################################################################################################ #

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.application_args[0] == Bytes("add_master"), add_master],
        [Txn.application_args[0] == Bytes("del_master"), del_master],
        [Txn.application_args[0] == Bytes("add_client"), add_client],
        [Txn.application_args[0] == Bytes("del_client"), del_client],
        [Txn.application_args[0] == Bytes("add_asa"), add_asa],
        [Txn.application_args[0] == Bytes("del_asa"), del_asa],
        [Txn.application_args[0] == Bytes("manage_network_fees"), manage_network_fees],
        [Txn.application_args[0] == Bytes("manage_asa_fees"), manage_asa_fees],
        [Txn.application_args[0] == Bytes("manage_arc200_fees"), manage_arc200_fees],
        [Txn.application_args[0] == Bytes("claim_network_fees"), claim_network_fees],
        [Txn.application_args[0] == Bytes("claim_asa_fees"), claim_asa_fees],
        [Txn.on_completion() == OnComplete.DeleteApplication, del_app]
    )

    return program
