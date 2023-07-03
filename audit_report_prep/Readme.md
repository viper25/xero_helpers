# Statement of Contributions

To prepare the Statement of Contributions, we need to download the members contributions for the year. The following steps will guide you through the process. 

> Note this has only active members, so if there are any that have left mid-year
manually adjust those lookups.

* Download the member contributions from the DDB table `stosc_xero_member_payments
` that holds this data. This data is updated daily via a cron job.
* Pivot this to a csv file that can be used to create the Statement of Contributions.
* Create the Statement of Contributions.