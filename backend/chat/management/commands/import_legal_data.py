from django.core.management.base import BaseCommand
import pandas as pd
from chat.models import LawDocument

class Command(BaseCommand):
    help = 'Import legal precedent data from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        
        try:
            # Read CSV file
            df = pd.read_csv(csv_file)
            self.stdout.write(f"📁 Loading {len(df)} records from {csv_file}")
            
            imported_count = 0
            skipped_count = 0
            
            for index, row in df.iterrows():
                try:
                    # Create LawDocument from CSV data
                    law_doc, created = LawDocument.objects.get_or_create(
                        document_id=str(row.get('판례일련번호', f'PREC_{index}')),
                        defaults={
                            'doc_type': 'PRECEDENT',
                            'title': str(row.get('사건명', 'Unknown Case')),
                            'content': f"사건번호: {row.get('사건번호', 'N/A')}\n"
                                     f"법원명: {row.get('법원명', 'N/A')}\n"
                                     f"사건종류: {row.get('사건종류명', 'N/A')}\n"
                                     f"판결유형: {row.get('판결유형', 'N/A')}\n"
                                     f"선고: {row.get('선고', 'N/A')}",
                            'source_url': str(row.get('판례상세링크', '')),
                            'enforcement_date': str(row.get('선고일자', '00000000')),
                            'case_number': str(row.get('사건번호', '')),
                            'court_name': str(row.get('법원명', ''))
                        }
                    )
                    
                    if created:
                        imported_count += 1
                    else:
                        skipped_count += 1
                        
                    if (imported_count + skipped_count) % 100 == 0:
                        self.stdout.write(f"Processed {imported_count + skipped_count} records...")
                        
                except Exception as e:
                    self.stdout.write(f"Error processing row {index}: {e}")
                    continue
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Import completed!\n'
                    f'📊 Imported: {imported_count} new records\n'
                    f'⏭️  Skipped: {skipped_count} existing records'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Import failed: {e}')
            )
