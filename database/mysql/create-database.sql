CREATE TABLE `users` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `username` varchar(31) NOT NULL,
  `email` varchar(255) UNIQUE NOT NULL,
  `password` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE `suburbs` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `suburb_name` varchar(63) NOT NULL,
  `postcode` int NOT NULL,
  `latitude` decimal(8,6) NOT NULL,
  `longitude` decimal(9,6) NOT NULL,
  `state_code` varchar(3) NOT NULL
);

CREATE TABLE `user_alert_time` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `start_time` time NOT NULL DEFAULT '00:00:00',
  `end_time` time NOT NULL DEFAULT '23:59:59',
  `is_active` bool NOT NULL DEFAULT true
);

CREATE TABLE `weather_cats` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `category` varchar(31) NOT NULL
);

CREATE TABLE `weathers` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `category_id` int NOT NULL,
  `weather` varchar(31) NOT NULL,
  `weather_code` int NOT NULL UNIQUE DEFAULT -1
);

CREATE TABLE `posts` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `latitude` decimal(8,6) NOT NULL,
  `longitude` decimal(9,6) NOT NULL,
  `suburb_id` int NOT NULL,
  `weather_id` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `likes` int NOT NULL DEFAULT 0,
  `views` int NOT NULL DEFAULT 0,
  `reports` int NOT NULL DEFAULT 0,
  `is_active` bool NOT NULL DEFAULT true,
  `comment` text
);

CREATE TABLE `user_like_post` (
  `user_id` int NOT NULL,
  `post_id` int NOT NULL,
  PRIMARY KEY (`user_id`, `post_id`)
);

CREATE TABLE `user_view_post` (
  `user_id` int NOT NULL,
  `post_id` int NOT NULL,
  PRIMARY KEY (`user_id`, `post_id`)
);

CREATE TABLE `user_report_post` (
  `user_id` int NOT NULL,
  `post_id` int NOT NULL,
  `report_comment` text NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`, `post_id`)
);

CREATE TABLE `user_alert_weather` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `weather_id` int NOT NULL
);

CREATE TABLE `user_alert_suburb` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `suburb_id` int NOT NULL
);

CREATE TABLE `user_saved_suburb` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `suburb_id` int NOT NULL,
  `label` varchar(15) NOT NULL
);

CREATE TABLE `user_fcm_tokens` (
    `id` int PRIMARY KEY AUTO_INCREMENT,
    `user_id` int NOT NULL,
    `fcm_token` VARCHAR(255) UNIQUE NOT NULL,
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX `suburbs_index_0` ON `suburbs` (`suburb_name`, `postcode`);

CREATE UNIQUE INDEX `user_alert_time_index_1` ON `user_alert_time` (`user_id`, `start_time`, `end_time`);

CREATE UNIQUE INDEX `weathers_index_2` ON `weathers` (`weather`, `weather_code`);

CREATE UNIQUE INDEX `user_alert_weather_index_3` ON `user_alert_weather` (`user_id`, `weather_id`);

CREATE UNIQUE INDEX `user_alert_suburb_index_4` ON `user_alert_suburb` (`user_id`, `suburb_id`);

CREATE UNIQUE INDEX `user_saved_suburb_index_5` ON `user_saved_suburb` (`user_id`, `label`);

ALTER TABLE `user_alert_time` ADD FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `weathers` ADD FOREIGN KEY (`category_id`) REFERENCES `weather_cats` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `posts` ADD FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

ALTER TABLE `posts` ADD FOREIGN KEY (`suburb_id`) REFERENCES `suburbs` (`id`) ON DELETE CASCADE;

ALTER TABLE `posts` ADD FOREIGN KEY (`weather_id`) REFERENCES `weathers` (`id`) ON DELETE CASCADE;

ALTER TABLE `user_like_post` ADD FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `user_like_post` ADD FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `user_view_post` ADD FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `user_view_post` ADD FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `user_report_post` ADD FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `user_report_post` ADD FOREIGN KEY (`post_id`) REFERENCES `posts` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `user_alert_weather` ADD FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `user_alert_weather` ADD FOREIGN KEY (`weather_id`) REFERENCES `weathers` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `user_alert_suburb` ADD FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `user_alert_suburb` ADD FOREIGN KEY (`suburb_id`) REFERENCES `suburbs` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `user_saved_suburb` ADD FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `user_saved_suburb` ADD FOREIGN KEY (`suburb_id`) REFERENCES `suburbs` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE `user_fcm_tokens` ADD FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

