import hashlib
import base64

def md5_hash_password(password):
    md5 = hashlib.md5()
    md5.update(password.encode('utf-8'))
    return md5.hexdigest()

# Replace 'passwords.txt' with the path to your password file
password_file = 'passwords.txt'

# Open the file and read passwords line by line
with open(password_file, 'r') as file:
    passwords = [line.strip() for line in file]

# Create a list to store the formatted and base64-encoded entries
output_list = []

for password in passwords:
    hashed_password = md5_hash_password(password)
    formatted_entry = f'admin:{hashed_password}'
    output_list.append(formatted_entry)

# Save the output to 'cookies.txt'
with open('cookies.txt', 'w') as output_file:
    for entry in output_list:
        # Encode the entry in base64
        encoded_entry = base64.b64encode(
            entry.encode('utf-8')
        ).decode('utf-8')
        output_file.write(encoded_entry + '\n')

