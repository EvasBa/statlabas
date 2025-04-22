# Statybos Marketplace Techninė Architektūra

## Backend (Django Oscar)

### Core Models
- User
  - BaseUser (AbstractUser)
    - user_type: private, business
  - CustomerProfile
    - private
    - business
  - VendorProfile
    - private
    - busines
    - Verification status
    - Business details
    - Rating

- Product
  - Title
  - Description
  - Category
  - Condition
  - Original price
  - Discounted price
  - Location
  - Quantity
  - Status (available, reserved, sold)
  - Images
  - shipping: pickup, delivery

- Order
  - Order number
  - User
  - Vendor
  - Items
  - Status
  - Payment status
  - Shipping details

### Core Services
1. Authentication Service
   - JWT based auth
   - Social auth integration
   - Role-based permissions

2. Payment Service
   - Payment gateway integration
   - Commission handling
   - Refund processing

3. Notification Service
   - Email notifications
   - In-app notifications
   - SMS notifications (optional)

## Frontend (Next.js + Tailwind)

### Core Components
1. Public Pages
   - Homepage with featured items
   - Product listing with filters
   - Product details
   - Vendor profiles
   - Registration/Login

2. User Dashboard
   - Order history
   - Saved items
   - Profile management
   - Messages

3. Vendor Dashboard
   - Product management
   - Order management
   - Analytics
   - Earnings

### State Management
- React Query for server state
- Context API for local state

## API Architecture

### RESTful Endpoints
1. Authentication
   - /api/auth/login
   - /api/auth/register
   - /api/auth/verify

2. Products
   - /api/products/
   - /api/products/{id}
   - /api/products/search
   - /api/products/categories

3. Orders
   - /api/orders/
   - /api/orders/{id}
   - /api/orders/status

4. Vendors
   - /api/vendors/
   - /api/vendors/{id}
   - /api/vendors/products

## Infrastructure

### Development
- Docker compose setup
- Local development environment
- Testing environment

### Production
- AWS recommended infrastructure
- S3 for media storage
- CloudFront for CDN
- RDS for database

## Security Measures
1. Input validation
2. XSS protection
3. CSRF protection
4. Rate limiting
5. Data encryption
6. Secure payment processing

## Monitoring and Analytics
1. Error tracking
2. Performance monitoring
3. User analytics
4. Sales metrics