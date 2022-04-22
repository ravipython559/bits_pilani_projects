RiskApproved = 'RiskApproved'
OutOfStock = 'OutOfStock'
BankAccountDetailsComplete = 'BankAccountDetailsComplete'
ApplicationInProgress = 'ApplicationInProgress'
CustomerCancelled = 'CustomerCancelled'
InArrears = 'InArrears'
WrittenOff = 'WrittenOff'
Closed = 'Closed'
Cancelled = 'Cancelled'
Approved = 'Approved'
Referred = 'Referred'
DocumentsComplete = 'DocumentsComplete'
DepositPaid = 'DepositPaid'
LoanAgreementAccepted = 'LoanAgreementAccepted'
Declined = 'Declined'
PreAccepted = 'PreAccepted'
TimeoutCancelled = 'TimeoutCancelled'
MerchantCancelled = 'MerchantCancelled'
RiskPending = 'RiskPending'
Active = 'Active'
TransactionInitiated = 'TransactionInitiated'

ZEST_STATUS_CHOICES = (
	(None, '-'),
	(RiskPending, RiskPending),
	(RiskApproved, RiskApproved),
	(OutOfStock, OutOfStock),
	(BankAccountDetailsComplete, BankAccountDetailsComplete),
	(ApplicationInProgress, ApplicationInProgress),
	(CustomerCancelled, CustomerCancelled),
	(InArrears, InArrears),
	(WrittenOff, WrittenOff),
	(Closed, Closed),
	(Cancelled, Cancelled),
	(Approved, Approved),
	(Referred, Referred),
	(DocumentsComplete, DocumentsComplete),
	(DepositPaid, DepositPaid),
	(LoanAgreementAccepted, LoanAgreementAccepted),
	(Declined, Declined),
	(PreAccepted, PreAccepted),
	(TimeoutCancelled, TimeoutCancelled),
	(MerchantCancelled, MerchantCancelled),
	(Active, Active),
	(TransactionInitiated, TransactionInitiated),
)

ZEST_DISPLAY_STATUS_CHOICES = (
	(None, '-'),
	(RiskPending, 'Risk Pending'),
	(RiskApproved, 'Risk Approved'),
	(OutOfStock, 'Out Of Stock'),
	(BankAccountDetailsComplete, 'Bank Account Details Complete'),
	(ApplicationInProgress, 'Application In Progress'),
	(CustomerCancelled, 'Customer Cancelled'),
	(InArrears, 'In Arrears'),
	(WrittenOff, 'Written Off'),
	(Closed, 'Closed'),
	(Cancelled, 'Cancelled'),
	(Approved, 'Approved'),
	(Referred, 'Referred'),
	(DocumentsComplete, 'Documents Complete'),
	(DepositPaid, 'Deposit Paid'),
	(LoanAgreementAccepted, 'Loan Agreement Accepted'),
	(Declined, 'Declined'),
	(PreAccepted, 'Pre Accepted'),
	(TimeoutCancelled, 'Timeout Cancelled'),
	(MerchantCancelled, 'Merchant Cancelled'),
	(Active, 'Active'),
	(TransactionInitiated, 'Transaction Initiated'),
)

cancelled_status = [MerchantCancelled, TimeoutCancelled, Cancelled, CustomerCancelled]

inprogress_status = [
	RiskPending, 
	PreAccepted, 
	LoanAgreementAccepted, 
	DepositPaid, 
	DocumentsComplete, 
	ApplicationInProgress, 
	BankAccountDetailsComplete, 
	RiskApproved,
	Approved,
	TransactionInitiated,
]

incancelled_status = [
	RiskPending, 
	PreAccepted, 
	DocumentsComplete, 
	ApplicationInProgress,
	BankAccountDetailsComplete,
	RiskApproved,
]


SUBMITTED = 'SUBMITTED'
APPROVED = 'APPROVED'
REJECTED = 'REJECTED'
ACTIVE = 'ACTIVE'
DISBURSED = 'DISBURSED'
DISBURSAL_FAILED = 'DISBURSAL_FAILED'
NewLoanApplication = 'New Loan Application'


EZCRED_DISPLAY_STATUS_CHOICES = (
	(None, '-'),
	(NewLoanApplication, 'New Loan Application'),
	(SUBMITTED, 'SUBMITTED'),
	(APPROVED, 'APPROVED'),
	(REJECTED, 'REJECTED'),
	(ACTIVE, 'ACTIVE'),
	(DISBURSED, 'DISBURSED'),
	(DISBURSAL_FAILED, 'DISBURSAL_FAILED'),
)

CREATED = 'CREATED'
READY_FOR_DISBURSAL = 'READY_FOR_DISBURSAL'
PUSHED_FOR_DISBURSAL = 'PUSHED_FOR_DISBURSAL'
DROPPED = 'DROPPED'

PROPELLD_DISPLAY_STATUS_CHOICES = (
	(None, '-'),
	(NewLoanApplication, 'New Loan Application'),
	(CREATED, 'CREATED'),
	(APPROVED, 'APPROVED'),
	(REJECTED, 'REJECTED'),
	(READY_FOR_DISBURSAL, 'READY_FOR_DISBURSAL'),
	(PUSHED_FOR_DISBURSAL, 'PUSHED_FOR_DISBURSAL'),
	(DISBURSED, 'DISBURSED'),
	(DROPPED, 'DROPPED'),
)