# Dev
# use the official Node.js image as the base image
FROM node:alpine AS build

# make the 'app' folder the current working directory
WORKDIR /app

# copy both 'package.json' and 'package-lock.json' (if available)
COPY package*.json ./

# install project dependencies
# RUN npm install

# copy project files and folders to the current working directory (i.e. 'app' folder)
COPY . .
EXPOSE 3001
# ENTRYPOINT [ "npm", "run", "dev" ]
ENTRYPOINT [ "sleep", "infinity" ]



# Release
# # Use the official Node.js image as the base image
# FROM node:alpine AS build

# # Set the working directory inside the container
# WORKDIR /app

# # Copy package.json and package-lock.json (if present)
# COPY package*.json ./

# # Install dependencies
# RUN npm install

# # Copy the rest of the application files
# COPY . .

# # Build the application for production with minification
# RUN npm run build

# # Use the lightweight nginx image to create the production build
# FROM nginx:alpine

# # Copy the built Vue.js application from the previous stage into the nginx image
# COPY --from=build /app/dist /usr/share/nginx/html

# # Expose port 80, which the application will run on
# EXPOSE 80

# # Command to start the nginx server
# CMD ["nginx", "-g", "daemon off;"]