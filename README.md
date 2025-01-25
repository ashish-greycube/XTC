## XGG

XGG customization to make automated supplier and salary payments via DBS Bank (Hong Kong) or Hang Seng (Hong Kong). This customisation allows for regular, automated payments of suppliers and upload a CSV file to the bank.

#### Installation (the HRMS module is required or installation will fail)

1. `bench get-app --branch version-15 https://github.com/ashish-greycube/XTC`
2. `bench --site sitename install-app xtc`
3. `bench --site sitename migrate`
4. `bench clear-cache`
5. `bench restart`
6. `sudo supervisorctl reload`

#### What does it do?

To avoid manually paying each supplier, avoiding the necessity to write, sign and submit/send out dozens of cheques, this customisation allows to pay multiple suppliers in one batch and upload the payment details comfortably via online banking to the bank. The payments need then be approved by an authorized person before they will be processed by the bank. It allows for a completely remote process without the supervisor being on site to sign cheques or approve (urgent) payments.

The app can handle two different bank file formats (Hang Seng, DBS Bank), although not simultaneously.

- Hang Seng Bank (Hong Kong) allows to upload one autopay file per day and category (supplier/salary) and processes the file once the transactions are approved.
- DBS Bank (Hong Kong) also allows to define up to five email addresses to receive a payment advice sent out by the bank. This customisation also allows to define the recipients as an optional setting.

Paying hundreds of invoices is literally a task of 5-10 minutes and saves a lot of manpower. In a first step, the user will select the payment details required for ERPNext (Mode of Payment, Payment Date) and some filter criteria for the invoices to be paid (i.e. due date). This provides then a list of invoices to process. Invoices can be manually edited/removed from the suggested list. A total amount is shown as well as the amount per supplier.

Once these details are validated, it can be finalized in 5 steps:
1. Create the Draft Payment Entry
2. Download the Bank CSV file (and then upload the file via your online banking to the bank)
3. Let ERPNext send out an automated email to the supervisor to approve the uploaded payment file in the online banking. The email contains some details for easy verification (total amount, number of transactions). This step is optional, if the supervisor uploads the file himself.
4. Let ERPNext send out an automated email to the suppliers, informing them of the payment made with a list of the invoices paid
5. Close the transaction

#### Necessary setup

1. Supplier record
Payment Details
- Supplier Party Account Type Hang Seng - The type of identifier for the FPS payment for Hang Seng bank files
- Supplier Party Account Type DBS - The type of identifier for the FPS payment for DBS bank files
- Supplier Party Bank Code      - The Hong Kong bank code. It's a three digit number and requires the leading zeros
- Supplier Party Account ID     - 
- Supplier Party Account Number - The value of the bank account number, FPS ID, email address of mobile number
- Supplier Party Name			- This is the bank account holder name and must correspond, or the bank might reject the transfer
<img src="https://i.ibb.co/RPGnLB4/Supplier.png">

Contacts
- Define which contacts (email addresses) should receive the notification email(s)

2. Accounts
The bank account number from which the payment is made needs to be entered in the corresponding Chart of Accounts account for the DBS payment file
<img src="https://i.ibb.co/TLRmRmm/Account.png">

4. Company
For the DBS payment file the Organisation ID is needed. There is a custom field in the company to provide that value
<img src="https://i.ibb.co/mcGNjVs/Company.png">

6. Payment Settings

To set the email templates and print formats used for the payment advices that are sent out
- Bank Payment Summary - The email being sent to the supervisor authorizing the bank payment
- Supplier Payment Advice - The email being sent to the supplier advising what was paid to them
- Default Bank Accounts used for the payments
- Email address where the bank payment summary is sent to
<img src="https://i.ibb.co/qp6wBST/Payment-Settings.png">

#### License

MIT

<hr>

#### Contact Us  

<a href="https://greycube.in"><img src="https://greycube.in/files/greycube_logo09eade.jpg" width="250" height="auto"></a> <br>
1<sup>st</sup> ERPNext [Certified Partner](https://frappe.io/api/method/frappe.utils.print_format.download_pdf?doctype=Certification&name=PARTCRTF00002&format=Partner%20Certificate&no_letterhead=0&letterhead=Blank&settings=%7B%7D&_lang=en#toolbar=0)
<sub> <img src="https://greycube.in/files/certificate.svg" width="20" height="20"> </sub>
& winner of the [Best Partner Award](https://frappe.io/partners/india/greycube-technologies) <sub> <img src="https://greycube.in/files/award.svg" width="25" height="25"> </sub>

<h5>
<sub><img src="https://greycube.in/files/link.svg" width="20" height="auto"> </sub> <a href="https://greycube.in"> greycube.in</a><br>
<sub><img src="https://greycube.in/files/8665305_envelope_email_icon.svg" width="20" height="18"> </sub> <a href="mailto:sales@greycube.in"> 
 sales@greycube.in</a><br>
<sub><img src="https://greycube.in/files/linkedin1.svg" width="20" height="18"> </sub> <a href="https://www.linkedin.com/company/greycube-technologies"> LinkedIn</a><br>
<sub><img src="https://greycube.in/files/blog.svg" width="20" height="18"> </sub><a href="https://greycube.in/blog"> Blogs</a> </h5>
