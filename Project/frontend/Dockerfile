FROM nginx:alpine

# copy all HTML/CSS/JS files to nginx serve directory
COPY . /usr/share/nginx/html

# copy nginx config for HTTPS
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 443