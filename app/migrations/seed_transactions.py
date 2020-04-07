import os
import random
import sys

from faker import Faker
from flask import g
from uuid import uuid4

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..", "..")))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))

import config

from server import bt
from server import create_app
from server import db
from server.models.credit_transfer import CreditTransfer
from server.models.organisation import Organisation
from server.models.user import User
from server.models.token import Token
from server.models.token import TokenType
from server.models.transfer_account import TransferAccount
from server.models.transfer_account import TransferAccountType
from server.models.transfer_usage import TransferUsage
from server.utils.user import create_transfer_account_user
from server.utils.transfer_enums import TransferTypeEnum
from server.utils.transfer_enums import TransferSubTypeEnum

fake = Faker()


def fund_account(address, amount_wei):
    from web3 import (
        Web3,
        HTTPProvider
    )

    w3 = Web3(HTTPProvider(config.ETH_HTTP_PROVIDER))

    tx_hash = w3.eth.sendTransaction(
        {'to': address, 'from': w3.eth.accounts[0], 'value': amount_wei})
    return w3.eth.waitForTransactionReceipt(tx_hash)


def _get_or_create_model_object(obj_class: db.Model, filter_kwargs: dict, **kwargs):
    instance = obj_class.query.filter_by(**filter_kwargs).first()

    if instance:
        return instance
    else:
        print('Creating new obj')
        instance = obj_class(**{**filter_kwargs, **kwargs})
        db.session.add(instance)
        return instance


def get_or_create_transfer_usage(name):
    return _get_or_create_model_object(TransferUsage, {'name': name})


def get_or_create_master_organization():
    organisation = Organisation.master_organisation()

    if not organisation:
        print('Creating master organisation ...')
        organisation = Organisation(name='Grassroots Economics', is_master=True)
        db.session.add(organisation)
        db.session.commit()
        print('Master Organisation {} created.'.format(organisation.name))
    else:
        print('Master organisation found, skipping ...')

    return organisation


def get_or_create_admin_user(email, password, admin_organisation):
    admin = User.query.filter_by(
        email=str(email).lower()).first()

    if admin:
        print('Admin user found, skipping ...')
    else:
        print('Creating admin user ...')
        admin = User(first_name='Admin', last_name='User')
        admin.create_admin_auth(
            email=email,
            password=password,
            tier='sempoadmin',
            organisation=admin_organisation
        )

        admin.is_activated = True
        db.session.add(admin)

        print('Admin user created.')

        print('Creating transfer account for admin user: {} {} ...'.format(admin.first_name, admin.last_name))

        transfer_account = TransferAccount(
            bound_entity=admin,
            blockchain_address=admin.primary_blockchain_address,
            organisation=admin_organisation
        )

        transfer_account.is_approved = True
        transfer_account.account_type = TransferAccountType.USER

        db.session.add(transfer_account)

    return admin


def get_or_create_reserve_token(deploying_address, name, symbol):
    token = Token.query.filter_by(symbol=symbol).first()

    if not token:
        print('Creating reserve token ...')

        reserve_token_address = bt.deploy_and_fund_reserve_token(
            deploying_address=deploying_address,
            name=name,
            symbol=symbol,
            fund_amount_wei=0
        )

        token = Token(
            address=reserve_token_address,
            name=name,
            symbol=symbol,
            token_type=TokenType.RESERVE
        )
        token.decimals = 18

        db.session.add(token)
        print('Reserve token: {} created.'.format(token.id))

    else:
        print('Reserve token found, skipping ...')

    return token


def create_user_with_transfer_account(email, business_usage, organisation):
    user = User.query.filter_by(
        email=str(email).lower()).first()

    if user:
        return user
    else:
        first_name = fake.first_name()
        last_name = fake.last_name()
        is_beneficiary = random.choice([True, False])

        phone = '+254' + ''.join([str(random.randint(1, 9)) for i in range(0, 9)])

        user = create_transfer_account_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            organisation=organisation,
            is_beneficiary=is_beneficiary,
            is_vendor=not is_beneficiary)

        user.business_usage = business_usage

    return user


def create_random_users(number_of_users: int, organisation: Organisation):
    counter = 1
    user_list = []
    transfer_usages = TransferUsage.query.all()
    while counter < number_of_users:
        random_usage = random.choice(transfer_usages)

        user = create_user_with_transfer_account(
            email=f'user-nr-{counter}@test.com',
            business_usage=random_usage,
            organisation=organisation
        )

        user_list.append(user)
        counter += 1

    return user_list


def create_transfer(amount, sender_user, recipient_user, token, subtype=None):
    transfer = CreditTransfer(
        amount=amount,
        sender_user=sender_user,
        recipient_user=recipient_user,
        token=token,
        uuid=str(uuid4()))

    db.session.add(transfer)

    transfer.resolve_as_completed()

    transfer.transfer_type = TransferTypeEnum.PAYMENT
    transfer.transfer_subtype = subtype

    db.session.commit()

    return transfer


def create_random_transfers(number_of_transfers, user_list, token):
    transfer_list = []
    i = 0
    while i < number_of_transfers:
        try:
            shuffled = user_list.copy()
            random.shuffle(shuffled)

            transfer = create_transfer(
                amount=random.randint(50000, 200000),
                sender_user=shuffled[0],
                recipient_user=shuffled[1],
                token=token
            )

            transfer.transfer_subtype = TransferSubTypeEnum.STANDARD

            transfer_list.append(transfer)
            i += 1
        except Exception as exception:
            print(exception)
            pass
    return transfer_list


def create_random_disbursements_to_users(user_list, admin_user, token):
    for user in user_list:
        amount = 40000
        create_transfer(
            amount=amount,
            sender_user=admin_user,
            recipient_user=user,
            token=token,
            subtype=TransferSubTypeEnum.DISBURSEMENT
        )

        print('Disbursing: {} Ksh. to {} {}'.format((amount/100), user.first_name, user.last_name))


def get_balance(wallet_address, token):
    balance = bt.get_wallet_balance(wallet_address, token)
    return balance


def get_or_create_float_wallet():
    transfer_account = TransferAccount.query.execution_options(show_all=True).filter(
        TransferAccount.account_type == TransferAccountType.FLOAT
    ).first()

    if not transfer_account:
        print('Creating float account ...')
        transfer_account = TransferAccount(
            private_key=config.ETH_FLOAT_PRIVATE_KEY,
            account_type=TransferAccountType.FLOAT,
            is_approved=True
        )
        db.session.add(transfer_account)
        print('Float wallet created: {}'.format(transfer_account.id))

    else:

        print('Float wallet already exists, skipping...')
    return transfer_account


if __name__ == "__main__":
    # provide flask context within which SQL queries can be executed.
    app = create_app()
    app_context = app.app_context()
    app_context.push()

    # set flask context to show all model data for easier querying using flask models.
    g.show_all = True

    # create master organisation
    master_organisation = get_or_create_master_organization()
    master_system_address = master_organisation.system_blockchain_address

    # fund master organisation account
    fund_account(master_system_address, int(500000e18))

    # create reserve token
    reserve_token = get_or_create_reserve_token(deploying_address=master_system_address,
                                                name='Kenyan Shilling',
                                                symbol='Ksh')

    master_organisation.token = reserve_token

    # create float wallet
    float_wallet = get_or_create_float_wallet()

    # fund float wallet
    print('Funding float wallet ...')
    fund_account(float_wallet.blockchain_address, int(500000e18))
    fund_float_wallet = bt.send_eth(
        signing_address=master_organisation.primary_blockchain_address,
        recipient_address=float_wallet.blockchain_address,
        amount_wei=500000 * int(1e18)
    )
    float_wallet.balance = 500000
    print('Float wallet funded: {} ETH'.format(500000))
    bt.await_task_success(fund_float_wallet)

    # create admin
    admin_user = get_or_create_admin_user('admin@withsempo.com', 'TestPassword', master_organisation)
    db.session.flush()
    admin_transfer_account = admin_user.transfer_account

    # fund admin account with money
    print('Funding admin transfer account ...')
    amount_to_load = 5000000
    fund_account(admin_user.primary_blockchain_address, int(5000000e18))
    fund_admin_account = bt.send_eth(
        signing_address=admin_transfer_account.blockchain_address,
        recipient_address=reserve_token.address,
        amount_wei=amount_to_load * int(1e18))

    admin_user.transfer_account.balance = amount_to_load
    print('Admin transfer account funded: {} ETH'.format(amount_to_load))
    bt.await_task_success(fund_admin_account)

    print('Creating Transfer Usage')
    usages = list(map(
        get_or_create_transfer_usage,
        ['Broken Pencils',
         'Off Milk',
         'Stuxnet',
         'Used Playing Cards',
         '09 F9',
         'Junk Mail',
         'Cutlery',
         'Leaked Private Keys',
         'Parking Infringements',
         'Betamax Movies',
         'Hyperallergenic Soap',
         'Dioxygen Difluoride',
         'Hunter2'
         ]))

    # create users
    user_list = create_random_users(20, master_organisation)

    # make disbursements
    create_random_disbursements_to_users(user_list=user_list, admin_user=admin_user, token=reserve_token)

    # seed transactions
    create_random_transfers(200, user_list, reserve_token)

    db.session.commit()

    app_context.pop()
