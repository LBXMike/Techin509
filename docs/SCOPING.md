# My assistant — scoping brief

## Objectives
The user is my partner, who will use the agent to search for information about fictitious purchases on receipts. Example questions:
- How much did I spend on 10/1/26?
- What items were bought this month?
- How much was this item?

## The gap / need

The user currently has to search through receipts by hand for information that a document retrieval tool could find much more quickly. A database query is limited in the type of information it can pull. A form doesn't help at all, and a dashboard only slightly speeds up the process.

## Key deliverables

A chatbot that can handle the information from 3 fictitious receipts, each with up to 5 items. The chatbot should be able to pull all purchasing data from each receipt, such as price, items, store, and date. It should also tell the user when it can't find the information. The first version is limited to the fictitious data provided.

## Data requirements & constraints

The first version of the chatbot is a proof of concept that uses 3 synthetic receipts stored in the repository at data/receipts/receipts.json. After this version is proven effective, more synthetic receipts will be added to continue testing. When distributed to users, real receipts will stay on the user's local drive and will not be added to the repository. What should never enter the repository is credit card information or other PII. To confirm this, the uploaded data will be verified by a human designer.

## Success measure

Observable test:
First-version success will be based on the chatbot being able to find information about the items listed on the receipts. How much did the milk cost? How many items came from Walmart? What did I get from Walmart?

Pass threshold:
Successfully identifying purchasing information for 10 of the 15 total items listed across the 3 receipts.

2 unsupported questions: What is the 16th item? Can you tell me what I bought on the 4th receipt?

## Peer review and revision

Not required for this assignment (the instructor waived peer review).
