"""
This file (kenya_ussd_state_machine.py) contains the KenyaUssdStateMachine responsible for managing the states of
the ussd application as would apply to its use in kenya.
It manages transitions between different states of the ussd system based on user input.
The class contains methods responsible for validation of user input and processing user input to facilitate
the services provided by the  ussd app.
"""
import re
from phonenumbers.phonenumberutil import NumberParseException
import math
import config

from transitions import Machine, State

from server import ussd_tasker
from server.utils.phone import send_message
from server.models.user import User, RegistrationMethodEnum
from server.models.ussd import UssdSession
from server.models.transfer_usage import TransferUsage
from server.utils.i18n import i18n_for
from server.utils.user import set_custom_attributes, change_initial_pin, change_current_pin, default_token, \
    get_user_by_phone, transfer_usages_for_user, send_terms_message_if_required, attach_transfer_account_to_user
from server.utils.credit_transfer import dollars_to_cents, cents_to_dollars
from server.utils.phone import proccess_phone_number

ITEMS_PER_MENU = 8
USSD_MAX_LENGTH = 164
MIN_EXCHANGE_AMOUNT_CENTS = 40


class KenyaUssdStateMachine(Machine):

    def __repr__(self):
        return f"<KenyaUssdStateMachine: {self.state}>"

    # define machine states
    states = [
        'feed_char',
        'start',
        'initial_language_selection',
        'initial_pin_entry',
        'initial_pin_confirmation',
        # send token states
        'send_enter_recipient',
        'send_token_amount',
        'send_token_reason',
        'send_token_reason_other',
        'send_token_pin_authorization',
        # account management states
        'account_management',
        'balance_inquiry_pin_authorization',
        'choose_language',
        'pin_change',
        'current_pin',
        'new_pin',
        'new_pin_confirmation',
        'about_me',
        'change_my_business_prompt',
        'opt_out_of_market_place_pin_authorization',
        # user profile state
        'user_profile',
        'first_name_entry',
        'last_name_entry',
        'gender_entry',
        'location_entry',
        'name_change_pin_authorization',
        'gender_change_pin_authorization',
        'location_change_pin_authorization',
        'bio_change_pin_authorization',
        'profile_info_change_pin_authorization',
        'view_profile_pin_authorization',
        # directory listing state
        'directory_listing',
        'directory_listing_other',
        # exchange token states
        'exchange_token',
        # 'exchange_rate_pin_authorization',
        'exchange_token_agent_number_entry',
        'exchange_token_amount_entry',
        'exchange_token_pin_authorization',
        'exchange_token_confirmation',
        # help state
        'help',
        # exit states
        'exit',
        'exit_not_registered',
        'exit_invalid_menu_option',
        'exit_invalid_recipient',
        'exit_invalid_input',
        'exit_use_exchange_menu',
        'exit_wrong_pin',
        'exit_invalid_pin',
        'exit_pin_mismatch',
        'exit_pin_blocked',
        'exit_invalid_token_agent',
        'exit_invalid_exchange_amount',
        'exit_account_creation_prompt',
        'exit_successful_send_token',
        State(name='complete', on_enter=['send_terms_to_user_if_required'])
    ]

    def send_sms(self, phone, message_key, **kwargs):
        message = i18n_for(self.user, "ussd.kenya.{}".format(message_key), **kwargs)
        send_message(phone, message)

    def change_preferred_language_to_sw(self, user_input):
        self.change_preferred_language_to("sw")

    def change_preferred_language_to_en(self, user_input):
        self.change_preferred_language_to("en")

    def change_preferred_language_to(self, language):
        self.user.preferred_language = language
        self.send_sms(self.user.phone, "language_change_sms")

    def initial_change_preferred_language_to_sw(self, user_input):
        self.initial_change_preferred_language_to("sw")

    def initial_change_preferred_language_to_en(self, user_input):
        self.initial_change_preferred_language_to("en")

    def initial_change_preferred_language_to(self, language):
        self.user.preferred_language = language

    def change_opted_in_market_status(self, user_input):
        self.user.is_market_enabled = False
        self.send_sms(self.user.phone, "opt_out_of_market_place_sms")

    def send_terms_to_user_if_required(self, user_inpt):
        send_terms_message_if_required(self.user)

    def set_phone_as_verified(self, user_input):
        self.user.is_phone_verified = True

    def save_pin_data(self, user_input):
        self.session.set_data('initial_pin', user_input)

    def add_first_name_to_session_data(self, user_input):
        self.session.set_data('first_name', user_input)

    def add_last_name_to_session_data(self, user_input):
        self.session.set_data('last_name', user_input)

    def add_gender_to_session_data(self, user_input):
        self.session.set_data('gender', user_input)

    def add_location_to_session_data(self, user_input):
        self.session.set_data('location', user_input)

    def add_bio_to_session_data(self, user_input):
        self.session.set_data('bio', user_input)

    def save_username_info(self, user_input):
        first_name = self.session.get_data('first_name')
        last_name = self.session.get_data('last_name')
        self.user.first_name = first_name
        self.user.last_name = last_name

    def save_gender_info(self, user_input):
        gender_selection = self.session.get_data('gender')
        gender = None
        if self.menu_one_selected(gender_selection):
            gender = 'male'
        if self.menu_two_selected(gender_selection):
            gender = 'female'

        attrs = {
            "custom_attributes": {
                "gender": gender
            }
        }
        set_custom_attributes(attrs, self.user)

    def save_location_info(self, user_input):
        location = self.session.get_data('location')
        self.user.location = location

    def save_business_directory_info(self, user_input):
        bio = self.session.get_data('bio')
        attrs = {
            "custom_attributes": {
                "bio": bio
            }
        }
        set_custom_attributes(attrs, self.user)

    def save_profile_info(self, user_input):
        # save name information
        self.save_username_info(user_input)

        # save bio information
        self.save_business_directory_info(user_input)

        # save gender info
        self.save_gender_info(user_input)

        # save location information
        self.save_location_info(user_input)

    def is_valid_pin(self, user_input):
        pin_validity = False
        if len(user_input) == 4 and re.match(r"\d", user_input):
            pin_validity = True
        return pin_validity

    def new_pins_match(self, user_input):
        pins_match = False
        # get previous pin input
        initial_pin = self.session.get_data('initial_pin')
        if user_input == initial_pin:
            pins_match = True
        return pins_match

    def authorize_pin(self, pin):
        authorized = False
        if self.user.failed_pin_attempts is None:
            self.user.failed_pin_attempts = 0
        if self.user.failed_pin_attempts >= 3:
            return False
        if self.user.failed_pin_attempts < 3:
            authorized = self.user.verify_pin(pin)
            if authorized:
                if self.user.failed_pin_attempts > 0:
                    self.user.failed_pin_attempts = 0
            else:
                self.user.failed_pin_attempts += 1
        return authorized

    def complete_initial_pin_change(self, user_input):
        try:
            change_initial_pin(user=self.user, new_pin=user_input)
        except Exception as e:
            self.send_sms(self.user.phone, "pin_change_error_sms")
            raise e

    def complete_pin_change(self, user_input):
        try:
            change_current_pin(user=self.user, new_pin=user_input)
            self.send_sms(self.user.phone, "pin_change_success_sms")
        except Exception as e:
            self.send_sms(self.user.phone, "pin_change_error_sms")
            raise e

    def is_authorized_pin(self, user_input):
        return self.authorize_pin(user_input)

    def is_blocked_pin(self, user_input):
        return self.user.failed_pin_attempts is not None and self.user.failed_pin_attempts == 3

    def is_valid_new_pin(self, user_input):
        return self.is_valid_pin(user_input) and not self.user.verify_pin(user_input)

    # recipient exists, is not initiator, matches active and agent requirements
    def is_valid_recipient(self, user, should_be_active, should_be_agent):
        return user is not None and \
               user.phone != self.user.phone and \
               user.is_disabled != should_be_active and \
               user.has_token_agent_role == should_be_agent

    def is_user(self, user_input):
        user = get_user_by_phone(user_input, "KE")
        return self.is_valid_recipient(user, True, False)

    def is_token_agent(self, user_input):
        user = get_user_by_phone(user_input, "KE")
        return self.is_valid_recipient(user, True, True)

    def save_recipient_phone(self, user_input):
        self.session.set_data('recipient_phone', user_input)

    def save_transaction_amount(self, user_input):
        self.session.set_data('transaction_amount', dollars_to_cents(user_input))

    def save_transaction_reason(self, user_input):
        chosen_transfer_usage = self.get_select_transfer_usage(user_input)

        transfer_reason = None
        if self.user.preferred_language is not None and chosen_transfer_usage.translations is not None:
            transfer_reason = chosen_transfer_usage.translations.get(self.user.preferred_language)
        if transfer_reason is None:
            transfer_reason = chosen_transfer_usage.name

        self.session.set_data('transaction_reason_i18n', transfer_reason)
        self.session.set_data('transaction_reason_id', chosen_transfer_usage.id)

    def set_usage_menu_number(self, user_input):
        current_menu_nr = self.session.get_data('usage_menu')
        if int(user_input) == 9:
            current_menu_nr = current_menu_nr + 1
            self.session.set_data('usage_menu', current_menu_nr)
        elif int(user_input) == 10:
            current_menu_nr = current_menu_nr - 1 if current_menu_nr > 0 else 0
            self.session.set_data('usage_menu', current_menu_nr)

    def process_send_token_request(self, user_input):
        user = get_user_by_phone(self.session.get_data('recipient_phone'), "KE")
        amount = float(self.session.get_data('transaction_amount'))
        ussd_tasker.send_token(self.user, recipient=user, amount=amount)

    def upsell_unregistered_recipient(self, user_input):
        try:
            recipient_phone = proccess_phone_number(user_input)
        except NumberParseException:
            return None

        self.send_sms(
            self.user.phone,
            'upsell_message_sender',
            recipient_phone=recipient_phone,
        )
        self.send_sms(
            recipient_phone,
            'upsell_message_recipient',
            first_name=self.user.first_name,
            last_name=self.user.last_name,
            token_name=default_token(self.user).name
        )

    def inquire_balance(self, user_input):
        ussd_tasker.inquire_balance(self.user)

    def send_directory_listing(self, user_input):
        chosen_transfer_usage = self.get_select_transfer_usage(user_input)
        ussd_tasker.send_directory_listing(self.user, chosen_transfer_usage)

    def fetch_user_exchange_rate(self, user_input):
        ussd_tasker.fetch_user_exchange_rate(self.user)

    def is_valid_token_agent(self, user_input):
        user = get_user_by_phone(user_input, "KE")
        return user is not None and user.has_token_agent_role

    def save_exchange_agent_phone(self, user_input):
        self.session.set_data('agent_phone', user_input)

    def is_valid_token_amount(self, user_input):
        try:
            return float(user_input) > 0
        except ValueError:
            return False

    def is_valid_token_exchange_amount(self, user_input):
        return float(user_input) * 100 >= MIN_EXCHANGE_AMOUNT_CENTS

    def is_valid_menu_option(self, user_input):
        try:
            return 0 <= int(user_input) <= 9
        except ValueError:
            return False

    def is_valid_other_menu_option(self, user_input):
        try:
            return 0 <= int(user_input) <= 10
        except ValueError:
            return False

    def save_exchange_amount(self, user_input):
        self.session.set_data('exchange_amount', dollars_to_cents(user_input))

    def process_exchange_token_request(self, user_input):
        agent = get_user_by_phone(self.session.get_data('agent_phone'), "KE")
        amount = float(self.session.get_data('exchange_amount'))
        ussd_tasker.exchange_token(self.user, agent, amount)

    @staticmethod
    def make_usage_mapping(usage: TransferUsage):
        return {'id': usage.id, 'translations': usage.translations, 'name': usage.name}

    def store_transfer_usage(self, user_input):
        usages = transfer_usages_for_user(self.user)
        transfer_usage_map = list(map(KenyaUssdStateMachine.make_usage_mapping, usages))

        self.session.set_data('transfer_usage_mapping', transfer_usage_map)
        self.session.set_data('usage_menu', 0)

    def get_select_transfer_usage(self, user_input):
        menu_page = self.session.get_data('usage_menu')
        usage_stack = self.session.get_data('usage_index_stack') or [0]
        idx = usage_stack[menu_page] + int(user_input) - 1
        selected_tranfer_usage_id = self.session.get_data('transfer_usage_mapping')[idx]['id']
        return TransferUsage.query.get(selected_tranfer_usage_id)

    def is_ussd_signup(self, user_input):
        return self.user.registration_method == RegistrationMethodEnum.USSD_SIGNUP

    def has_empty_name_info(self, user_input):
        if self.user.first_name == 'Unknown first name' or not \
                self.user.first_name or \
                self.user.last_name == 'Unknown last name' or not \
                self.user.last_name:
            return True
        else:
            return False

    def has_empty_gender_info(self, user_input):
        gender = next(filter(lambda x: x.name == 'gender', self.user.custom_attributes), None)
        if not gender or gender.value.strip('"') == 'Unknown gender':
            return True
        else:
            return False

    def has_empty_location_info(self, user_input):
        if not self.user.location or self.user.location == 'Unknown location':
            return True
        else:
            return False

    def has_empty_bio_info(self, user_input):
        bio = next(filter(lambda x: x.name == 'bio', self.user.custom_attributes), None)
        if not bio or bio.value.strip('"') == 'Unknown business':
            return True
        else:
            return False

    def has_complete_profile(self, user_input):
        if not self.has_empty_name_info(user_input) and not \
                self.has_empty_bio_info(user_input) and not \
                self.has_empty_gender_info(user_input) and not \
                self.has_empty_location_info(user_input):
            return True
        else:
            return False

    def is_admin_pin_reset(self, user_input):
        pin_reset_tokens = self.user.pin_reset_tokens or []
        valid_reset_tokens = []
        for reset_token in pin_reset_tokens:
            if self.user.is_pin_reset_token_valid(reset_token):
                valid_reset_tokens.append(reset_token)
        has_valid_reset_tokens = len(valid_reset_tokens) > 0
        return has_valid_reset_tokens

    def process_account_creation_request(self, user_input):
        try:
            attach_transfer_account_to_user(self.user)
            disbursement_amount = cents_to_dollars(config.SELF_SERVICE_WALLET_INITIAL_DISBURSEMENT)
            self.send_sms(self.user.phone,
                          "account_creation_success_sms",
                          disbursement_amount=disbursement_amount,
                          token_name=default_token(self.user).name)
        except Exception as e:
            self.send_sms(self.user.phone, "account_creation_error_sms")
            raise Exception('Account creation failed. Error: ', e)

    def menu_one_selected(self, user_input):
        return user_input == '1'

    def menu_two_selected(self, user_input):
        return user_input == '2'

    def menu_three_selected(self, user_input):
        return user_input == '3'

    def menu_four_selected(self, user_input):
        return user_input == '4'

    def menu_five_selected(self, user_input):
        return user_input == '5'

    def menu_nine_selected(self, user_input):
        return user_input == '9'

    def menu_ten_selected(self, user_input):
        return user_input == '10'

    # initialize machine
    def __init__(self, session: UssdSession, user: User):
        self.session = session
        self.user = user
        Machine.__init__(
            self,
            model=self,
            states=self.states,
            initial=session.state
        )

        # event: initial_language_selection transitions
        initial_language_selection_transitions = [
            {'trigger': 'feed_char',
             'source': 'initial_language_selection',
             'dest': 'initial_pin_entry',
             'after': 'initial_change_preferred_language_to_en',
             'conditions': 'menu_one_selected'},
            {'trigger': 'feed_char',
             'source': 'initial_language_selection',
             'dest': 'initial_pin_entry',
             'after': 'initial_change_preferred_language_to_sw',
             'conditions': 'menu_two_selected'},
            {'trigger': 'feed_char',
             'source': 'initial_language_selection',
             'dest': 'help',
             'conditions': 'menu_three_selected'},
            {'trigger': 'feed_char',
             'source': 'initial_language_selection',
             'dest': 'exit_invalid_menu_option'}
        ]
        self.add_transitions(initial_language_selection_transitions)

        # event: initial_pin_entry transitions
        initial_pin_entry_transitions = [
            {'trigger': 'feed_char',
             'source': 'initial_pin_entry',
             'dest': 'initial_pin_confirmation',
             'after': 'save_pin_data',
             'conditions': 'is_valid_pin'},
            {'trigger': 'feed_char',
             'source': 'initial_pin_entry',
             'dest': 'exit_invalid_pin'}
        ]
        self.add_transitions(initial_pin_entry_transitions)

        # event: initial_pin_confirmation transitions
        initial_pin_confirmation_transitions = [
            {'trigger': 'feed_char',
             'source': 'initial_pin_confirmation',
             'dest': 'exit_account_creation_prompt',
             'unless': 'is_admin_pin_reset',
             'after': ['complete_initial_pin_change', 'set_phone_as_verified', 'send_terms_to_user_if_required',
                       'process_account_creation_request'],
             'conditions': ['is_ussd_signup', 'new_pins_match']},
            {'trigger': 'feed_char',
             'source': 'initial_pin_confirmation',
             'dest': 'start',
             'conditions': ['new_pins_match', 'is_admin_pin_reset'],
             'after': 'complete_initial_pin_change'},
            {'trigger': 'feed_char',
             'source': 'initial_pin_confirmation',
             'dest': 'start',
             'after': ['complete_initial_pin_change', 'set_phone_as_verified', 'send_terms_to_user_if_required'],
             'conditions': 'new_pins_match'},
            {'trigger': 'feed_char',
             'source': 'initial_pin_confirmation',
             'dest': 'exit_pin_mismatch'}
        ]
        self.add_transitions(initial_pin_confirmation_transitions)

        # event: start transitions
        start_transitions = [
            {'trigger': 'feed_char',
             'source': 'start',
             'dest': 'send_enter_recipient',
             'conditions': 'menu_one_selected'},
            {'trigger': 'feed_char',
             'source': 'start',
             'dest': 'account_management',
             'conditions': 'menu_two_selected'},
            {'trigger': 'feed_char',
             'source': 'start',
             'dest': 'directory_listing',
             'conditions': 'menu_three_selected',
             'after': 'store_transfer_usage'},
            {'trigger': 'feed_char',
             'source': 'start',
             'dest': 'exchange_token',
             'conditions': 'menu_four_selected'},
            {'trigger': 'feed_char',
             'source': 'start',
             'dest': 'help',
             'conditions': 'menu_five_selected'},
            {'trigger': 'feed_char',
             'source': 'start',
             'dest': 'exit_invalid_menu_option'}
        ]
        self.add_transitions(start_transitions)

        # event: send_enter_recipient transitions
        send_enter_recipient_transitions = [
            {'trigger': 'feed_char',
             'source': 'send_enter_recipient',
             'dest': 'send_token_amount',
             'conditions': 'is_user',
             'after': 'save_recipient_phone'},
            {'trigger': 'feed_char',
             'source': 'send_enter_recipient',
             'dest': 'exit_use_exchange_menu',
             'conditions': 'is_token_agent'},
            {'trigger': 'feed_char',
             'source': 'send_enter_recipient',
             'dest': 'exit_invalid_recipient',
             'after': 'upsell_unregistered_recipient'}
        ]
        self.add_transitions(send_enter_recipient_transitions)

        # event: send_token_amount transitions
        send_token_amount_transitions = [
            {'trigger': 'feed_char',
             'source': 'send_token_amount',
             'dest': 'send_token_pin_authorization',
             'conditions': 'is_valid_token_amount',
             'after': ['save_transaction_amount', 'store_transfer_usage']},
            {'trigger': 'feed_char',
             'source': 'send_token_amount',
             'dest': 'exit_invalid_input'},
        ]
        self.add_transitions(send_token_amount_transitions)

        # event: send_token_reason transitions
        send_token_reason_transitions = [
            {'trigger': 'feed_char',
             'source': 'send_token_reason',
             'dest': 'send_token_reason_other',
             'conditions': 'menu_nine_selected',
             'after': 'set_usage_menu_number'},
            {'trigger': 'feed_char',
             'source': 'send_token_reason',
             'dest': 'send_token_pin_authorization',
             'after': 'save_transaction_reason',
             'conditions': 'is_valid_menu_option'},
            {'trigger': 'feed_char',
             'source': 'send_token_reason',
             'dest': 'exit_invalid_menu_option'},
            {'trigger': 'feed_char',
             'source': 'send_token_reason_other',
             'dest': 'send_token_reason_other',
             'conditions': 'menu_nine_selected',
             'after': 'set_usage_menu_number'},
            {'trigger': 'feed_char',
             'source': 'send_token_reason_other',
             'dest': 'send_token_reason_other',
             'conditions': 'menu_ten_selected',
             'after': 'set_usage_menu_number'},
            {'trigger': 'feed_char',
             'source': 'send_token_reason_other',
             'dest': 'send_token_pin_authorization',
             'after': 'save_transaction_reason',
             'conditions': 'is_valid_other_menu_option'},
            {'trigger': 'feed_char',
             'source': 'send_token_reason_other',
             'dest': 'exit_invalid_menu_option'},
        ]
        self.add_transitions(send_token_reason_transitions)

        directory_listing_transitions = [
            {'trigger': 'feed_char',
             'source': 'directory_listing',
             'dest': 'directory_listing_other',
             'conditions': 'menu_nine_selected',
             'after': 'set_usage_menu_number'},
            {'trigger': 'feed_char',
             'source': 'directory_listing',
             'dest': 'complete',
             'after': 'send_directory_listing',
             'conditions': 'is_valid_menu_option'},
            {'trigger': 'feed_char',
             'source': 'directory_listing',
             'dest': 'exit_invalid_menu_option'},
            {'trigger': 'feed_char',
             'source': 'directory_listing_other',
             'dest': 'directory_listing_other',
             'conditions': 'menu_nine_selected',
             'after': 'set_usage_menu_number'},
            {'trigger': 'feed_char',
             'source': 'directory_listing_other',
             'dest': 'directory_listing_other',
             'conditions': 'menu_ten_selected',
             'after': 'set_usage_menu_number'},
            {'trigger': 'feed_char',
             'source': 'directory_listing_other',
             'dest': 'complete',
             'after': 'send_directory_listing',
             'conditions': 'is_valid_other_menu_option'},
            {'trigger': 'feed_char',
             'source': 'directory_listing_other',
             'dest': 'exit_invalid_menu_option'},
        ]
        self.add_transitions(directory_listing_transitions)

        # event: send_token_pin_authorization transitions
        send_token_pin_authorization_transitions = [
            {'trigger': 'feed_char',
             'source': 'send_token_pin_authorization',
             'dest': 'exit_successful_send_token',
             'conditions': 'is_authorized_pin',
             'after': 'process_send_token_request'},
            {'trigger': 'feed_char',
             'source': 'send_token_pin_authorization',
             'dest': 'exit_pin_blocked',
             'conditions': 'is_blocked_pin'}
        ]
        self.add_transitions(send_token_pin_authorization_transitions)

        # event: account_management transitions
        account_management_transitions = [
            {'trigger': 'feed_char',
             'source': 'account_management',
             'dest': 'user_profile',
             'conditions': 'menu_one_selected'},
            {'trigger': 'feed_char',
             'source': 'account_management',
             'dest': 'choose_language',
             'conditions': 'menu_two_selected'},
            {'trigger': 'feed_char',
             'source': 'account_management',
             'dest': 'balance_inquiry_pin_authorization',
             'conditions': 'menu_three_selected'},
            {'trigger': 'feed_char',
             'source': 'account_management',
             'dest': 'current_pin',
             'conditions': 'menu_four_selected'},
            {'trigger': 'feed_char',
             'source': 'account_management',
             'dest': 'opt_out_of_market_place_pin_authorization',
             'conditions': 'menu_five_selected'},
            {'trigger': 'feed_char',
             'source': 'account_management',
             'dest': 'exit_invalid_menu_option'}
        ]
        self.add_transitions(account_management_transitions)

        # event: user_profile transitions
        user_profile_transitions = [
            {'trigger': 'feed_char',
             'source': 'user_profile',
             'dest': 'first_name_entry',
             'conditions': 'menu_one_selected'},
            {'trigger': 'feed_char',
             'source': 'user_profile',
             'dest': 'gender_entry',
             'conditions': 'menu_two_selected'},
            {'trigger': 'feed_char',
             'source': 'user_profile',
             'dest': 'location_entry',
             'conditions': 'menu_three_selected'},
            {'trigger': 'feed_char',
             'source': 'user_profile',
             'dest': 'change_my_business_prompt',
             'conditions': 'menu_four_selected'},
            {'trigger': 'feed_char',
             'source': 'user_profile',
             'dest': 'view_profile_pin_authorization',
             'conditions': 'menu_five_selected'},
            {'trigger': 'feed_char',
             'source': 'user_profile',
             'dest': 'exit_invalid_menu_option'}
        ]
        self.add_transitions(user_profile_transitions)

        # event: choose_language transition
        choose_language_transitions = [
            {'trigger': 'feed_char',
             'source': 'choose_language',
             'dest': 'complete',
             'after': 'change_preferred_language_to_en',
             'conditions': 'menu_one_selected'},
            {'trigger': 'feed_char',
             'source': 'choose_language',
             'dest': 'complete',
             'after': 'change_preferred_language_to_sw',
             'conditions': 'menu_two_selected'},
            {'trigger': 'feed_char',
             'source': 'choose_language',
             'dest': 'exit_invalid_menu_option'}
        ]
        self.add_transitions(choose_language_transitions)

        # event: balance_inquiry_pin_authorization transitions
        balance_inquiry_pin_authorization_transitions = [
            {'trigger': 'feed_char',
             'source': 'balance_inquiry_pin_authorization',
             'dest': 'complete',
             'conditions': 'is_authorized_pin',
             'after': 'inquire_balance'
             },
            {'trigger': 'feed_char',
             'source': 'balance_inquiry_pin_authorization',
             'dest': 'exit_pin_blocked',
             'conditions': 'is_blocked_pin'}
        ]
        self.add_transitions(balance_inquiry_pin_authorization_transitions)

        # event: current_pin transitions
        current_pin_transitions = [
            {'trigger': 'feed_char',
             'source': 'current_pin',
             'dest': 'new_pin',
             'conditions': 'is_authorized_pin'},
            {'trigger': 'feed_char',
             'source': 'current_pin',
             'dest': 'exit_pin_blocked',
             'conditions': 'is_blocked_pin'}
        ]
        self.add_transitions(current_pin_transitions)

        # event: new_pin transitions
        new_pin_transitions = [
            {'trigger': 'feed_char',
             'source': 'new_pin',
             'dest': 'new_pin_confirmation',
             'after': 'save_pin_data',
             'conditions': 'is_valid_new_pin'},
            {'trigger': 'feed_char',
             'source': 'new_pin',
             'dest': 'exit_invalid_pin'}
        ]
        self.add_transitions(new_pin_transitions)

        # event: new_pin_confirmation transitions
        new_pin_confirmation = [
            {'trigger': 'feed_char',
             'source': 'new_pin_confirmation',
             'dest': 'complete',
             'conditions': 'new_pins_match',
             'after': 'complete_pin_change'},
            {'trigger': 'feed_char',
             'source': 'new_pin_confirmation',
             'dest': 'exit_pin_mismatch'}
        ]
        self.add_transitions(new_pin_confirmation)

        # event: opt_out_of_market_place_pin_authorization transitions
        opt_out_of_market_place_pin_authorization_transitions = [
            {'trigger': 'feed_char',
             'source': 'opt_out_of_market_place_pin_authorization',
             'dest': 'complete',
             'conditions': 'is_authorized_pin',
             'after': 'change_opted_in_market_status'},
            {'trigger': 'feed_char',
             'source': 'opt_out_of_market_place_pin_authorization',
             'dest': 'exit_pin_blocked',
             'conditions': 'is_blocked_pin'}
        ]
        self.add_transitions(opt_out_of_market_place_pin_authorization_transitions)

        # first_name_entry transitions
        self.add_transition(trigger='feed_char',
                            source='first_name_entry',
                            dest='last_name_entry',
                            after='add_first_name_to_session_data')

        # last_name_entry transitions
        last_name_entry_transitions = [
            # if profile is complete change last name and authorize..
            {'trigger': 'feed_char',
             'source': 'last_name_entry',
             'dest': 'name_change_pin_authorization',
             'conditions': 'has_complete_profile',
             'after': 'add_last_name_to_session_data'},

            # if profile is complete save for last_name_entry change last name and authorize.
            {'trigger': 'feed_char',
             'source': 'last_name_entry',
             'dest': 'name_change_pin_authorization',
             'conditions': 'has_empty_name_info',
             'unless': ['has_complete_profile', 'has_empty_gender_info', 'has_empty_location_info', 'has_empty_bio_info'],
             'after': 'add_last_name_to_session_data'},

            # if gender info is empty proceed to gender entry menu
            {'trigger': 'feed_char',
             'source': 'last_name_entry',
             'dest': 'gender_entry',
             'conditions': 'has_empty_gender_info',
             'after': 'add_last_name_to_session_data'},

            # if location info is empty and gender info is filled proceed to location entry menu
            {'trigger': 'feed_char',
             'source': 'last_name_entry',
             'dest': 'location_entry',
             'unless': 'has_empty_gender_info',
             'conditions': 'has_empty_location_info',
             'after': 'add_last_name_to_session_data'},

            # if business info is empty and gender and location info is filled proceed to business_entry menu
            {'trigger': 'feed_char',
             'source': 'last_name_entry',
             'dest': 'change_my_business_prompt',
             'unless': ['has_empty_gender_info', 'has_empty_location_info'],
             'conditions': 'has_empty_bio_info',
             'after': 'add_last_name_to_session_data'}
        ]
        self.add_transitions(last_name_entry_transitions)

        # gender_entry transitions
        gender_entry_transitions = [
            # if profile is complete, edit gender_entry and authorize.
            {'trigger': 'feed_char',
             'source': 'gender_entry',
             'dest': 'gender_change_pin_authorization',
             'conditions': 'has_complete_profile',
             'after': 'add_gender_to_session_data'},

            # if profile is complete save for gender_entry change gender and authorize.
            {'trigger': 'feed_char',
             'source': 'gender_entry',
             'dest': 'gender_change_pin_authorization',
             'conditions': 'has_empty_gender_info',
             'unless': ['has_complete_profile', 'has_empty_name_info', 'has_empty_location_info', 'has_empty_location_info'],
             'after': 'add_gender_to_session_data'},

            # if location info is empty proceed to location entry menu
            {'trigger': 'feed_char',
             'source': 'gender_entry',
             'dest': 'location_entry',
             'conditions': 'has_empty_location_info',
             'after': 'add_gender_to_session_data'},

            # if business info is empty and gender and location info is filled proceed to business_entry menu
            {'trigger': 'feed_char',
             'source': 'gender_entry',
             'dest': 'change_my_business_prompt',
             'unless': 'has_empty_location_info',
             'conditions': 'has_empty_bio_info'}
        ]
        self.add_transitions(gender_entry_transitions)

        # location_entry_transitions
        location_entry_transitions = [
            # if profile is complete, edit location_entry and authorize.
            {'trigger': 'feed_char',
             'source': 'location_entry',
             'dest': 'location_change_pin_authorization',
             'conditions': 'has_complete_profile',
             'after': 'add_location_to_session_data'},

            # if profile is complete save for location_entry change location and authorize.
            {'trigger': 'feed_char',
             'source': 'location_entry',
             'dest': 'location_change_pin_authorization',
             'conditions': 'has_empty_location_info',
             'unless': ['has_complete_profile', 'has_empty_name_info', 'has_empty_gender_info', 'has_empty_bio_info'],
             'after': 'add_location_to_session_data'},

            # if bio info is empty proceed to bio entry menu
            {'trigger': 'feed_char',
             'source': 'location_entry',
             'dest': 'change_my_business_prompt',
             'conditions': 'has_empty_bio_info',
             'after': 'add_location_to_session_data'},

        ]
        self.add_transitions(location_entry_transitions)

        # change_my_business_prompt_transitions
        change_my_business_prompt_transitions = [
            # if profile is complete, edit change_my_business_prompt and authorize.
            {'trigger': 'feed_char',
             'source': 'change_my_business_prompt',
             'dest': 'bio_change_pin_authorization',
             'conditions': 'has_complete_profile',
             'after': 'add_bio_to_session_data'},

            # if bio info is empty proceed to bio entry menu
            {'trigger': 'feed_char',
             'source': 'change_my_business_prompt',
             'dest': 'profile_info_change_pin_authorization',
             'conditions': 'has_empty_bio_info',
             'after': 'add_bio_to_session_data'},

        ]
        self.add_transitions(change_my_business_prompt_transitions)

        # name_change_pin_authorization transitions
        self.add_transition(trigger='feed_char',
                            source='name_change_pin_authorization',
                            dest='exit',
                            after='save_username_info')

        # gender_change_pin_authorization transitions
        self.add_transition(trigger='feed_char',
                            source='gender_change_pin_authorization',
                            dest='exit',
                            after='save_gender_info')

        # location_change_pin_authorization transitions
        self.add_transition(trigger='feed_char',
                            source='location_change_pin_authorization',
                            dest='exit',
                            after='save_location_info')

        # bio_change_pin_authorization transitions
        self.add_transition(trigger='feed_char',
                            source='bio_change_pin_authorization',
                            dest='exit',
                            after='save_bio_info')

        # profile_info_change_pin_authorization transitions
        self.add_transition(trigger='feed_char',
                            source='profile_info_change_pin_authorization',
                            dest='exit',
                            after='save_profile_info')

        # view_profile_pin_authorization transitions
        self.add_transition(trigger='feed_char',
                            source='view_profile_pin_authorization',
                            dest='about_me')

        # event: exchange_token transitions
        exchange_token_transitions = [
            {'trigger': 'feed_char',
             'source': 'exchange_token',
             'dest': 'complete',
             'conditions': 'menu_one_selected',
             'after': 'fetch_user_exchange_rate'},
            {'trigger': 'feed_char',
             'source': 'exchange_token',
             'dest': 'exchange_token_agent_number_entry',
             'conditions': 'menu_two_selected'},
            {'trigger': 'feed_char',
             'source': 'exchange_token',
             'dest': 'exit_invalid_menu_option'}
        ]
        self.add_transitions(exchange_token_transitions)

        # DEPRECATED - exchange rate currently given without requiring pin
        # event: exchange_rate_pin_authorization transitions
        exchange_rate_pin_authorization_transitions = [
            {'trigger': 'feed_char',
             'source': 'exchange_rate_pin_authorization',
             'dest': 'complete',
             'conditions': 'is_authorized_pin',
             'after': 'fetch_user_exchange_rate'},
            {'trigger': 'feed_char',
             'source': 'exchange_rate_pin_authorization',
             'dest': 'exit_pin_blocked',
             'conditions': 'is_blocked_pin'}
        ]
        self.add_transitions(exchange_rate_pin_authorization_transitions)

        # event: exchange_token_agent_number_entry transitions
        exchange_token_agent_number_entry_transitions = [
            {'trigger': 'feed_char',
             'source': 'exchange_token_agent_number_entry',
             'dest': 'exchange_token_amount_entry',
             'conditions': 'is_valid_token_agent',
             'after': 'save_exchange_agent_phone'},
            {'trigger': 'feed_char',
             'source': 'exchange_token_agent_number_entry',
             'dest': 'exit_invalid_token_agent'}
        ]
        self.add_transitions(exchange_token_agent_number_entry_transitions)

        # event: exchange_token_amount_entry transitions
        exchange_token_amount_entry_transitions = [
            {'trigger': 'feed_char',
             'source': 'exchange_token_amount_entry',
             'dest': 'exchange_token_pin_authorization',
             'conditions': ['is_valid_token_amount', 'is_valid_token_exchange_amount'],
             'after': 'save_exchange_amount'},
            {'trigger': 'feed_char',
             'source': 'exchange_token_amount_entry',
             'dest': 'exit_invalid_exchange_amount'}
        ]
        self.add_transitions(exchange_token_amount_entry_transitions)

        # event: exchange_token_pin_authorization transitions
        exchange_token_pin_authorization_transitions = [
            {'trigger': 'feed_char',
             'source': 'exchange_token_pin_authorization',
             'dest': 'exchange_token_confirmation',
             'conditions': 'is_authorized_pin'},
            {'trigger': 'feed_char',
             'source': 'exchange_token_pin_authorization',
             'dest': 'exit_pin_blocked',
             'conditions': 'is_blocked_pin'}
        ]
        self.add_transitions(exchange_token_pin_authorization_transitions)

        # event: exchange_token_confirmation transitions
        exchange_token_confirmation_transitions = [
            {'trigger': 'feed_char',
             'source': 'exchange_token_confirmation',
             'dest': 'complete',
             'conditions': 'menu_one_selected',
             'after': 'process_exchange_token_request'},
            {'trigger': 'feed_char',
             'source': 'exchange_token_confirmation',
             'dest': 'exit',
             'conditions': 'menu_two_selected'},
            {'trigger': 'feed_char',
             'source': 'exchange_token_confirmation',
             'dest': 'exit_invalid_menu_option'}
        ]
        self.add_transitions(exchange_token_confirmation_transitions)
