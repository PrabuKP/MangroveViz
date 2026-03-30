# Panduan Functional Point Analysis dengan PHPLoc & PHPMetric

## Persiapan Environment

### 1. Install PHP dan Composer
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install php-cli php-xml php-mbstring php-zip composer

# macOS dengan Homebrew
brew install php composer

# Windows dengan Chocolatey
choco install php composer
```

### 2. Install Tools Analisis
```bash
# Via Composer (global)
composer global require phploc/phploc
composer global require phpmetrics/phpmetrics

# Atau download PHAR files
wget https://phar.phpunit.de/phploc.phar
wget https://github.com/phpmetrics/PhpMetrics/releases/download/v2.4.1/phpmetrics.phar

# Buat executable
chmod +x phploc.phar phpmetrics.phar
sudo mv phploc.phar /usr/local/bin/phploc
sudo mv phpmetrics.phar /usr/local/bin/phpmetrics
```

### 3. Setup Project PHP
```bash
# Buat project baru
composer init

# Atau untuk project existing
cd /path/to/php/project
composer require --dev phploc/phploc phpmetrics/phpmetrics
```

## Penggunaan PHPLoc

### Basic Usage
```bash
# Analisis direktori
phploc src/

# Analisis dengan output JSON
phploc --log-json=phploc.json src/

# Analisis dengan progress bar
phploc --progress src/

# Exclude directories
phploc --exclude=vendor --exclude=tests src/
```

### Output PHPLoc
PHPLoc memberikan metrics:
- **Lines of Code (LOC)**: Total baris kode
- **Cyclomatic Complexity**: Kompleksitas siklomatik
- **Number of Classes/Interfaces**: Jumlah class dan interface
- **Number of Methods**: Jumlah method
- **Code Coverage**: Coverage testing

### Contoh Output
```
phploc 7.0.2 by Sebastian Bergmann.

Directories:                                          1
Files:                                               18

Size
  Lines of Code (LOC):                             617
  Comment Lines of Code (CLOC):                      89
  Non-Comment Lines of Code (NCLOC):               528
  Logical Lines of Code (LLOC):                     312

Complexity
  Cyclomatic Complexity / Number of Methods:      2.45
  Cyclomatic Complexity / Lines of Code:          0.13

Dependencies
  Global Accesses:                                  45
  Global Constants:                                  0
  Global Variables:                                  0
  Super-Global Variables:                            0

Structure
  Namespaces:                                         1
  Interfaces:                                          0
  Traits:                                              0
  Classes:                                            12
  Abstract Classes:                                    0
  Concrete Classes:                                   12
  Methods:                                            45
  Non-Static Methods:                                 42
  Static Methods:                                      3
  Public Methods:                                     40
  Non-Public Methods:                                  5
  Functions:                                           0
  Named Functions:                                     0
  Anonymous Functions:                                 0
```

## Penggunaan PHPMetric

### Basic Usage
```bash
# Analisis direktori
phpmetrics --report-html=metrics src/

# Analisis dengan format JSON
phpmetrics --report-json=metrics.json src/

# Analisis dengan violations
phpmetrics --violations src/

# Custom rules
phpmetrics --config=phpmetrics.json src/
```

### Output PHPMetric
PHPMetric memberikan analisis mendalam:
- **Maintainability Index**: Indeks maintainability
- **Technical Debt**: Hutang teknis
- **Cyclomatic Complexity**: Kompleksitas per method
- **Halstead Metrics**: Volume, difficulty, effort
- **Code Violations**: Pelanggaran coding standards

### Contoh Output HTML Report
```
├── index.html (Dashboard utama)
├── violations.html (Code violations)
├── complexity.html (Complexity analysis)
├── maintainability.html (Maintainability index)
├── barcharts.html (Charts dan graphs)
└── assets/ (CSS, JS, images)
```

## Metodologi Functional Point Analysis

### 1. Identifikasi Function Types

#### External Input (EI)
- Form submissions
- File uploads
- API POST/PUT requests
- Data entry forms

#### External Output (EO)
- Reports
- API responses
- Email notifications
- File downloads

#### External Inquiry (EQ)
- Search forms
- API GET requests
- Data queries
- Status checks

#### Internal Logical Files (ILF)
- Database tables
- Configuration files
- Cache storage
- Session data

#### External Interface Files (EIF)
- External APIs
- Third-party services
- File imports
- Data feeds

### 2. Complexity Assessment

#### Data Element Types (DET)
- Input fields
- Output fields
- Database columns
- API parameters

#### File Type Referenced (FTR)
- Number of files/tables referenced
- External systems accessed

#### Complexity Matrix
```
Low Complexity:    DET: 1-4,   FTR: 0-1
Average Complexity: DET: 5-15, FTR: 2-3
High Complexity:    DET: 16+,  FTR: 4+
```

### 3. Function Point Calculation

#### Unadjusted Function Points (UFP)
```
UFP = Σ(EI × Weight) + Σ(EO × Weight) + Σ(EQ × Weight) + Σ(ILF × Weight) + Σ(EIF × Weight)
```

#### Weights by Complexity
| Type | Low | Average | High |
|------|-----|---------|------|
| EI   | 3   | 4       | 6    |
| EO   | 4   | 5       | 7    |
| EQ   | 3   | 4       | 6    |
| ILF  | 7   | 10      | 15   |
| EIF  | 5   | 7       | 10   |

#### Value Adjustment Factor (VAF)
```
VAF = 0.65 + (0.01 × Degree of Influence)
```

Degree of Influence factors (0-5 scale):
1. Data communications
2. Distributed processing
3. Performance objectives
4. Heavily used configuration
5. Transaction rate
6. Online data entry
7. End-user efficiency
8. Online update
9. Complex processing
10. Reusability
11. Installation ease
12. Operational ease
13. Multiple sites
14. Facilitate change

### 4. Productivity Metrics

#### Lines of Code per Function Point
- Assembly: 320 LOC/FP
- C: 150 LOC/FP
- Java: 55 LOC/FP
- PHP: 50-65 LOC/FP
- Python: 40-50 LOC/FP

#### Effort Estimation
```
Effort (person-months) = AFP ÷ Productivity Rate
Productivity Rate ≈ 8-12 FP per person-month
```

## Contoh Analisis untuk PHP Project

### 1. E-commerce Website
```bash
# Analisis kode
phploc app/
phpmetrics --report-html=metrics app/

# Function Point Count
EI: User registration (4 FP), Product search (3 FP), Add to cart (4 FP)
EO: Order confirmation (5 FP), Invoice (7 FP)
EQ: Product catalog (4 FP), Order status (3 FP)
ILF: Users table (10 FP), Products table (10 FP), Orders table (10 FP)
EIF: Payment gateway (7 FP), Shipping API (5 FP)

Total UFP: 82 FP
VAF: 1.05 (DI = 40)
AFP: 86 FP
```

### 2. Content Management System
```bash
# Analisis kode
phploc src/
phpmetrics --report-html=metrics src/

# Function Point Count
EI: Create post (4 FP), Upload media (4 FP)
EO: RSS feed (5 FP), Sitemap (4 FP)
EQ: Search content (3 FP), Category filter (3 FP)
ILF: Posts table (10 FP), Users table (10 FP), Media table (7 FP)
EIF: Social media APIs (7 FP), Analytics (5 FP)

Total UFP: 75 FP
VAF: 0.95 (DI = 30)
AFP: 71 FP
```

## Best Practices

### 1. Regular Analysis
- Jalankan analisis setiap sprint/release
- Track metrics over time
- Identify improvement areas

### 2. Quality Gates
- Set thresholds untuk complexity
- Monitor maintainability index
- Review code violations

### 3. Integration dengan CI/CD
```yaml
# .github/workflows/analysis.yml
name: Code Analysis
on: [push, pull_request]
jobs:
  analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup PHP
        uses: shivammathur/setup-php@v2
        with:
          php-version: '8.1'
      - name: Install dependencies
        run: composer install
      - name: Run PHPLoc
        run: phploc src/ --log-json=phploc.json
      - name: Run PHPMetric
        run: phpmetrics --report-html=metrics src/
      - name: Upload artifacts
        uses: actions/upload-artifact@v2
        with:
          name: code-metrics
          path: |
            phploc.json
            metrics/
```

### 4. Custom Rules
```json
// phpmetrics.json
{
  "rules": {
    "cyclomaticComplexity": {
      "max": 10
    },
    "maintainabilityIndex": {
      "min": 50
    },
    "halsteadVolume": {
      "max": 1000
    }
  }
}
```

## Kesimpulan

Functional Point Analysis dengan PHPLoc dan PHPMetric memberikan:
- **Objective measurement** ukuran fungsional aplikasi
- **Quality metrics** untuk maintainability dan complexity
- **Productivity tracking** untuk estimasi effort
- **Technical debt identification** untuk improvement planning

Dengan tools ini, development teams dapat membuat keputusan yang lebih informed tentang project planning, resource allocation, dan quality improvement initiatives.