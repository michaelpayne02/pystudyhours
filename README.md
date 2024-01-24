Python scraper for the MyGreekStudy app

The script utilizes cookies to store login session tokens and save them to a pickle file. The docker container is configured to run the script hourly using alpine's crontab. [PHP defaults](<https://www.php.net/manual/en/session.configuration.php#:~:text=Defaults%20to%201440%20(24%20minutes).>) suggest that these should expire after 24 minutes, giving no benefit to saving cookies on disk. But they seem to last for at least 24 hours, thereby removing the need to log in on every run of the script.
