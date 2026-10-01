# Data quality notes

I checked the four supplied FORESIGHT CSV files and ran the cleaning pipeline.

- Sales: 36,550 rows
- Products: 50 SKUs
- Calendar: 731 dates
- Inventory: 4,800 snapshots
- The pipeline found no exact duplicate rows or unmatched sales SKUs/dates.
- Holiday and promotion-event labels are blank for some calendar dates. I treated these as “not recorded” and will not assume they mean no event happened.

The cleaned files and detailed counts are saved in `data/processed/` and `data_quality_report.json`.
## Inventory data limitations

The inventory file contains 200 SKUs, while the sales and product files contain 50. Only 50 inventory SKUs match the sales and product data; the other 150 cannot be linked to product details or sales. Inventory recommendations will cover only the 50 matched SKUs.

The latest inventory snapshot is dated 1 December 2025, while sales data runs through 31 December 2025. Recommendations must show the inventory snapshot date and should not describe those stock figures as current.