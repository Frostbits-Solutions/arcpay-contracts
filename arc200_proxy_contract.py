from pyteal import *
from subroutine import app_addr_from_id


def approval_program_arc200(master_app_id, arc200_app_id):
    on_create = Seq(
        App.globalPut(Bytes('master_app_id'), Int(master_app_id)),
        App.globalPut(Bytes('arc200_app_id'), Int(arc200_app_id)),
        App.globalPut(Bytes('total_client'), Int(0)),
        Approve()
    )

    add_client = Seq(
        master_sender := App.globalGetEx(App.globalGet(Bytes('master_app_id')), Concat(Bytes('m_'), Txn.sender())),
        Assert(master_sender.hasValue()),
        If(
            master_sender.value() == Txn.sender()
        ).Then(
            App.globalPut(Txn.application_args[1], Int(1)),
            Approve()
        ),
        Reject()
    )

    del_client = Seq(
        master_sender := App.globalGetEx(App.globalGet(Bytes('master_app_id')), Concat(Bytes('m_'), Txn.sender())),
        Assert(master_sender.hasValue()),
        If(
            master_sender.value() == Txn.sender()
        ).Then(
            App.globalDel(Txn.application_args[1]),
            Approve()
        ),
        Reject()
    )

    add_fees = Seq(
        # Check sender is the main contrat
        Assert(Txn.sender() == app_addr_from_id(App.globalGet(Bytes('master_app_id')))),
        If(
            # Check client has more than 0 as fees
            App.globalGet(Txn.application_args[1]) > Int(0)
        ).Then(
            # update the amount of fees of the client
            App.globalPut(
                Txn.application_args[1],
                Add(Btoi(Txn.application_args[2]), App.globalGet(Txn.application_args[1]))
            ),
            # update the amount of total client
            App.globalPut(
                Bytes('total_client'),
                Add(Btoi(Txn.application_args[2]), App.globalGet(Bytes('total_client')))
            )
        ),
        Approve()
    )

    add_fees_test = Seq(
        If(
            # Check client has more than 0 as fees
            App.globalGet(Txn.application_args[1]) > Int(0)
        ).Then(
            # update the amount of fees of the client
            App.globalPut(
                Txn.application_args[1],
                Add(Btoi(Txn.application_args[2]), App.globalGet(Txn.application_args[1]))
            ),
            # update the amount of total client
            App.globalPut(
                Bytes('total_client'),
                Add(Btoi(Txn.application_args[2]), App.globalGet(Bytes('total_client')))
            )
        ),
        Approve()
    )

    remove_fees = Seq(
        # Check sender is the main contrat Txn.sender()
        Assert(Txn.sender() == app_addr_from_id(App.globalGet(Bytes('master_app_id')))),
        If(
            # Check client has more than 0 as fees
            App.globalGet(Txn.application_args[1]) > Int(0)
        ).Then(
            # Decrease the total amount for client from what was sent
            App.globalPut(
                Bytes('total_client'),
                Minus(
                    App.globalGet(Bytes('total_client')),
                    Minus(App.globalGet(Txn.application_args[1]), Int(1))
                )
            ),
            # Put fees to client to default value (1)
            App.globalPut(
                Txn.application_args[1],
                Int(1)
            )
        ),
        Approve()
    )

    on_delete = Seq(
        Assert(Txn.sender() == Global.creator_address()),
        Approve()
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete],
        [Txn.application_args[0] == Bytes("test"), Approve()],
        [Txn.application_args[0] == Bytes("add_client"), add_client],
        [Txn.application_args[0] == Bytes("del_client"), del_client],
        [Txn.application_args[0] == Bytes("add_fees"), add_fees],
        [Txn.application_args[0] == Bytes("add_fees_test"), add_fees_test],
        [Txn.application_args[0] == Bytes("remove_fees"), remove_fees],
    )

    return program