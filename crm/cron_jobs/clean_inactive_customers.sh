#!/bin/bash

# Navigate to the Django project root (adjust path if needed)
cd "$(dirname "$0")/../.."

# Activate virtual environment if required
# source venv/bin/activate

# Run Django shell command to delete inactive customers
DELETED_COUNT=$(python manage.py shell -c "
import datetime
from crm.models import Customer, Order

one_year_ago = datetime.date.today() - datetime.timedelta(days=365)
inactive_customers = Customer.objects.exclude(order__created_at__gte=one_year_ago)
count = inactive_customers.count()
inactive_customers.delete()
print(count)
")

# Log with timestamp
echo \"\$(date '+%Y-%m-%d %H:%M:%S') - Deleted \$DELETED_COUNT inactive customers\" >> /tmp/customer_cleanup_log.txt
