from Helpers import helpers


def email_count(email_count, module):
    """
    Print the number of gathered emails with a module-specific message.

    Parameters:
    email_count (int): The number of emails gathered.
    module (str): The name of the module.
    """
    try:
        message = f" [*] {module}: Gathered {email_count} Email(s)!"
        print(helpers.color(message, status=True))
    except Exception as e:
        print(helpers.color(f" [!] Error in email_count function: {e}", warning=True))
