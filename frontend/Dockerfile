# Start from official Node.js 20 Alpine image
FROM node:20-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the package.json file into the container
COPY package.json .
RUN npm install

# Copy the rest of the application code into the container
COPY . .

# Expose the port the application will run on
EXPOSE 3000

# Run the application
CMD ["npm", "run", "dev"]
