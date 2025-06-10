const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Create necessary directories
const directories = [
  'src',
  'src/config',
  'src/controllers',
  'src/middleware',
  'src/models',
  'src/routes',
  'src/utils'
];

directories.forEach(dir => {
  const dirPath = path.join(__dirname, dir);
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
    console.log(`Created directory: ${dir}`);
  }
});

// Create .env file if it doesn't exist
const envPath = path.join(__dirname, '.env');
if (!fs.existsSync(envPath)) {
  const envContent = `NODE_ENV=development
PORT=5000
MONGODB_URI=mongodb://localhost:27017/flowcast
JWT_SECRET=your_jwt_secret_key_here
JWT_EXPIRE=30d
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX=100`;

  fs.writeFileSync(envPath, envContent);
  console.log('Created .env file');
}

// Install dependencies
console.log('Installing dependencies...');
try {
  execSync('npm install', { stdio: 'inherit' });
  console.log('Dependencies installed successfully');
} catch (error) {
  console.error('Error installing dependencies:', error);
  process.exit(1);
}

console.log('\nProject initialization completed successfully!');
console.log('\nNext steps:');
console.log('1. Update the .env file with your configuration');
console.log('2. Start the development server with: npm run dev'); 