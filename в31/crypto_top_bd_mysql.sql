-- phpMyAdmin SQL Dump
-- version 5.1.1deb5ubuntu1
-- https://www.phpmyadmin.net/
--
-- Хост: localhost
-- Время создания: Июн 15 2025 г., 00:56
-- Версия сервера: 8.0.42-0ubuntu0.22.04.1
-- Версия PHP: 8.1.2-1ubuntu2.21

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- База данных: `crypto_top_bd_mysql`
--

-- --------------------------------------------------------

--
-- Структура таблицы `balances`
--

CREATE TABLE `balances` (
  `id` int NOT NULL,
  `currency` varchar(10) NOT NULL,
  `total` float NOT NULL,
  `free` float NOT NULL,
  `used` float NOT NULL,
  `timestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Дамп данных таблицы `balances`
--

INSERT INTO `balances` (`id`, `currency`, `total`, `free`, `used`, `timestamp`) VALUES
(1, 'USDT', 10000, 10000, 0, '2025-06-14 06:11:56'),
(2, 'USDT', 10000, 10000, 0, '2025-06-14 06:12:24'),
(3, 'USDT', 10000, 10000, 0, '2025-06-14 06:40:04'),
(4, 'USDT', 10000, 10000, 0, '2025-06-14 06:40:34'),
(5, 'USDT', 10000, 10000, 0, '2025-06-14 06:40:52'),
(6, 'USDT', 10000, 10000, 0, '2025-06-14 08:17:57'),
(7, 'USDT', 10000, 10000, 0, '2025-06-14 08:18:32'),
(8, 'USDT', 10000, 10000, 0, '2025-06-14 08:18:37'),
(9, 'USDT', 10000, 10000, 0, '2025-06-14 08:18:41'),
(10, 'USDT', 10000, 10000, 0, '2025-06-14 08:18:46'),
(11, 'USDT', 10000, 10000, 0, '2025-06-14 08:18:50'),
(12, 'USDT', 10000, 10000, 0, '2025-06-14 08:18:55'),
(13, 'USDT', 10000, 10000, 0, '2025-06-14 08:38:12'),
(14, 'USDT', 10000, 10000, 0, '2025-06-14 08:38:42'),
(15, 'USDT', 10000, 10000, 0, '2025-06-14 08:38:46'),
(16, 'USDT', 10000, 10000, 0, '2025-06-14 08:38:50'),
(17, 'USDT', 10000, 10000, 0, '2025-06-14 08:38:56'),
(18, 'USDT', 10000, 10000, 0, '2025-06-14 08:38:59'),
(19, 'USDT', 10000, 10000, 0, '2025-06-14 08:39:04'),
(20, 'USDT', 10000, 10000, 0, '2025-06-14 08:39:10'),
(21, 'USDT', 10000, 10000, 0, '2025-06-14 09:16:04'),
(22, 'USDT', 10000, 10000, 0, '2025-06-14 13:52:20'),
(23, 'USDT', 10000, 10000, 0, '2025-06-14 13:53:24'),
(24, 'USDT', 10000, 10000, 0, '2025-06-14 13:53:53'),
(25, 'USDT', 10000, 10000, 0, '2025-06-14 13:54:04'),
(26, 'USDT', 10000, 10000, 0, '2025-06-14 13:54:08'),
(27, 'USDT', 10000, 10000, 0, '2025-06-14 13:54:18'),
(28, 'USDT', 10000, 10000, 0, '2025-06-14 13:54:32'),
(29, 'USDT', 10000, 10000, 0, '2025-06-14 13:54:35'),
(30, 'USDT', 10000, 10000, 0, '2025-06-14 13:54:40'),
(31, 'USDT', 10000, 10000, 0, '2025-06-14 13:54:46'),
(32, 'USDT', 10000, 10000, 0, '2025-06-14 13:54:48'),
(33, 'USDT', 10000, 10000, 0, '2025-06-14 13:54:51'),
(34, 'USDT', 10000, 10000, 0, '2025-06-14 13:54:57'),
(35, 'USDT', 10000, 10000, 0, '2025-06-14 13:55:03'),
(36, 'USDT', 10000, 10000, 0, '2025-06-14 13:55:11'),
(37, 'USDT', 10000, 10000, 0, '2025-06-14 13:55:17'),
(38, 'USDT', 10000, 10000, 0, '2025-06-14 13:55:23'),
(39, 'USDT', 10000, 10000, 0, '2025-06-14 13:55:35'),
(40, 'USDT', 10000, 10000, 0, '2025-06-14 13:55:38'),
(41, 'USDT', 10000, 10000, 0, '2025-06-14 13:55:42'),
(42, 'USDT', 10000, 10000, 0, '2025-06-14 13:55:44'),
(43, 'USDT', 10000, 10000, 0, '2025-06-14 13:55:49'),
(44, 'USDT', 10000, 10000, 0, '2025-06-14 13:55:51'),
(45, 'USDT', 10000, 10000, 0, '2025-06-14 14:01:06'),
(46, 'USDT', 10000, 10000, 0, '2025-06-14 14:01:35'),
(47, 'USDT', 10000, 10000, 0, '2025-06-14 14:01:57'),
(48, 'USDT', 10000, 10000, 0, '2025-06-14 14:02:15'),
(49, 'USDT', 10000, 10000, 0, '2025-06-14 14:02:45');

-- --------------------------------------------------------

--
-- Структура таблицы `bot_settings`
--

CREATE TABLE `bot_settings` (
  `id` int NOT NULL,
  `key` varchar(50) NOT NULL,
  `value` text,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `description` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `bot_state`
--

CREATE TABLE `bot_state` (
  `id` int NOT NULL,
  `is_running` tinyint(1) DEFAULT '0',
  `start_time` timestamp NULL DEFAULT NULL,
  `stop_time` timestamp NULL DEFAULT NULL,
  `total_trades` int DEFAULT '0',
  `profitable_trades` int DEFAULT '0',
  `total_profit` float DEFAULT '0',
  `current_balance` float DEFAULT '0',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Дамп данных таблицы `bot_state`
--

INSERT INTO `bot_state` (`id`, `is_running`, `start_time`, `stop_time`, `total_trades`, `profitable_trades`, `total_profit`, `current_balance`, `updated_at`) VALUES
(1, 0, '2025-06-14 14:01:32', '2025-06-14 14:03:04', 0, 0, 0, 10000, '2025-06-14 14:03:04');

-- --------------------------------------------------------

--
-- Структура таблицы `signals`
--

CREATE TABLE `signals` (
  `id` int NOT NULL,
  `symbol` varchar(20) NOT NULL,
  `action` varchar(10) NOT NULL,
  `confidence` float NOT NULL,
  `price` float NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `executed` tinyint(1) DEFAULT '0',
  `stop_loss` float DEFAULT NULL,
  `take_profit` float DEFAULT NULL,
  `strategy` varchar(50) DEFAULT NULL,
  `reason` text,
  `executed_at` timestamp NULL DEFAULT NULL,
  `trade_id` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Дамп данных таблицы `signals`
--

INSERT INTO `signals` (`id`, `symbol`, `action`, `confidence`, `price`, `created_at`, `executed`, `stop_loss`, `take_profit`, `strategy`, `reason`, `executed_at`, `trade_id`) VALUES
(1, 'ETHUSDT', 'SELL', 0.833333, 3502.5, '2025-06-14 08:18:05', 0, 3654.3, 3274.8, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(2, 'ADAUSDT', 'SELL', 0.833333, 0.71, '2025-06-14 08:18:17', 0, 0.72953, 0.680705, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(3, 'ETHUSDT', 'SELL', 0.833333, 3502.5, '2025-06-14 08:18:32', 0, 3654.3, 3274.8, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(4, 'ADAUSDT', 'SELL', 0.833333, 0.71, '2025-06-14 08:18:32', 0, 0.72953, 0.680705, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(5, 'ETHUSDT', 'SELL', 0.833333, 3502.5, '2025-06-14 08:18:37', 0, 3654.3, 3274.8, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(6, 'ADAUSDT', 'SELL', 0.833333, 0.71, '2025-06-14 08:18:37', 0, 0.72953, 0.680705, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(7, 'ETHUSDT', 'SELL', 0.833333, 3502.5, '2025-06-14 08:18:41', 0, 3654.3, 3274.8, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(8, 'ADAUSDT', 'SELL', 0.833333, 0.71, '2025-06-14 08:18:41', 0, 0.72953, 0.680705, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(9, 'ETHUSDT', 'SELL', 0.833333, 3502.5, '2025-06-14 08:18:46', 0, 3654.3, 3274.8, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(10, 'ADAUSDT', 'SELL', 0.833333, 0.71, '2025-06-14 08:18:46', 0, 0.72953, 0.680705, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(11, 'ETHUSDT', 'SELL', 0.833333, 3502.5, '2025-06-14 08:18:50', 0, 3654.3, 3274.8, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(12, 'ADAUSDT', 'SELL', 0.833333, 0.71, '2025-06-14 08:18:50', 0, 0.72953, 0.680705, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(13, 'ETHUSDT', 'SELL', 0.833333, 3502.5, '2025-06-14 08:18:55', 0, 3654.3, 3274.8, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(14, 'ADAUSDT', 'SELL', 0.833333, 0.71, '2025-06-14 08:18:56', 0, 0.72953, 0.680705, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(15, 'ETHUSDT', 'SELL', 0.833333, 3444.17, '2025-06-14 08:38:23', 0, 3572.63, 3251.48, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(16, 'ADAUSDT', 'BUY', 0.875, 0.71, '2025-06-14 08:38:31', 0, 0.69548, 0.73178, 'multi_indicator', 'RSI: Перепроданность; MACD: Бычье пересечение; Stochastic: Перепроданность + пересечение', NULL, NULL),
(17, 'DOTUSDT', 'BUY', 0.833333, 3.7976, '2025-06-14 08:38:39', 0, 3.66702, 3.99347, 'multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(18, 'ETHUSDT', 'SELL', 0.833333, 3444.17, '2025-06-14 08:38:42', 0, 3572.63, 3251.48, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(19, 'ADAUSDT', 'BUY', 0.875, 0.71, '2025-06-14 08:38:43', 0, 0.69548, 0.73178, 'multi_indicator', 'RSI: Перепроданность; MACD: Бычье пересечение; Stochastic: Перепроданность + пересечение', NULL, NULL),
(20, 'DOTUSDT', 'BUY', 0.833333, 3.7976, '2025-06-14 08:38:43', 0, 3.66702, 3.99347, 'multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(21, 'ETHUSDT', 'SELL', 0.833333, 3444.17, '2025-06-14 08:38:46', 0, 3572.63, 3251.48, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(22, 'ADAUSDT', 'BUY', 0.875, 0.71, '2025-06-14 08:38:46', 0, 0.69548, 0.73178, 'multi_indicator', 'RSI: Перепроданность; MACD: Бычье пересечение; Stochastic: Перепроданность + пересечение', NULL, NULL),
(23, 'DOTUSDT', 'BUY', 0.833333, 3.7976, '2025-06-14 08:38:46', 0, 3.66702, 3.99347, 'multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(24, 'ETHUSDT', 'SELL', 0.833333, 3444.17, '2025-06-14 08:38:50', 0, 3572.63, 3251.48, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(25, 'ADAUSDT', 'BUY', 0.875, 0.71, '2025-06-14 08:38:51', 0, 0.69548, 0.73178, 'multi_indicator', 'RSI: Перепроданность; MACD: Бычье пересечение; Stochastic: Перепроданность + пересечение', NULL, NULL),
(26, 'DOTUSDT', 'BUY', 0.833333, 3.7976, '2025-06-14 08:38:51', 0, 3.66702, 3.99347, 'multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(27, 'ETHUSDT', 'SELL', 0.833333, 3444.17, '2025-06-14 08:38:56', 0, 3572.63, 3251.48, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(28, 'ADAUSDT', 'BUY', 0.875, 0.71, '2025-06-14 08:38:56', 0, 0.69548, 0.73178, 'multi_indicator', 'RSI: Перепроданность; MACD: Бычье пересечение; Stochastic: Перепроданность + пересечение', NULL, NULL),
(29, 'DOTUSDT', 'BUY', 0.833333, 3.7976, '2025-06-14 08:38:56', 0, 3.66702, 3.99347, 'multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(30, 'ETHUSDT', 'SELL', 0.833333, 3444.17, '2025-06-14 08:38:59', 0, 3572.63, 3251.48, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(31, 'ADAUSDT', 'BUY', 0.875, 0.71, '2025-06-14 08:38:59', 0, 0.69548, 0.73178, 'multi_indicator', 'RSI: Перепроданность; MACD: Бычье пересечение; Stochastic: Перепроданность + пересечение', NULL, NULL),
(32, 'DOTUSDT', 'BUY', 0.833333, 3.7976, '2025-06-14 08:38:59', 0, 3.66702, 3.99347, 'multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(33, 'ETHUSDT', 'SELL', 0.833333, 3444.17, '2025-06-14 08:39:04', 0, 3572.63, 3251.48, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(34, 'ADAUSDT', 'BUY', 0.875, 0.71, '2025-06-14 08:39:04', 0, 0.69548, 0.73178, 'multi_indicator', 'RSI: Перепроданность; MACD: Бычье пересечение; Stochastic: Перепроданность + пересечение', NULL, NULL),
(35, 'DOTUSDT', 'BUY', 0.833333, 3.7976, '2025-06-14 08:39:04', 0, 3.66702, 3.99347, 'multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(36, 'ETHUSDT', 'SELL', 0.833333, 3444.17, '2025-06-14 08:39:10', 0, 3572.63, 3251.48, 'multi_indicator', 'MACD: Медвежье пересечение; EMA: Нисходящий тренд; ADX: Сильный нисходящий тренд', NULL, NULL),
(37, 'ADAUSDT', 'BUY', 0.875, 0.71, '2025-06-14 08:39:10', 0, 0.69548, 0.73178, 'multi_indicator', 'RSI: Перепроданность; MACD: Бычье пересечение; Stochastic: Перепроданность + пересечение', NULL, NULL),
(38, 'DOTUSDT', 'BUY', 0.833333, 3.7976, '2025-06-14 08:39:10', 0, 3.66702, 3.99347, 'multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(39, 'BNBUSDT', 'BUY', 0.833333, 717, '2025-06-14 13:52:33', 0, 681.15, 788.7, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(40, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:53:18', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(41, 'BNBUSDT', 'BUY', 0.833333, 717, '2025-06-14 13:53:24', 0, 681.15, 788.7, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(42, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:53:51', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(43, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:02', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(44, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:04', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(45, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:15', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(46, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:26', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(47, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:32', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(48, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:35', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(49, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:40', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(50, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:46', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(51, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:48', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(52, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:51', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(53, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:54:57', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(54, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:09', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(55, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:11', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(56, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:21', 0, 3.5156, 3.5666, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(57, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:29', 0, 3.51706, 3.56441, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(58, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:35', 0, 3.51706, 3.56441, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(59, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:38', 0, 3.51706, 3.56441, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(60, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:42', 0, 3.51706, 3.56441, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(61, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:44', 0, 3.51706, 3.56441, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(62, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:49', 0, 3.51706, 3.56441, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(63, 'XRPUSDT', 'BUY', 0.833333, 3.536, '2025-06-14 13:55:51', 0, 3.51706, 3.56441, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(64, 'BNBUSDT', 'BUY', 0.833333, 710, '2025-06-14 14:01:17', 0, 674.5, 781, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(65, 'XRPUSDT', 'BUY', 0.833333, 3.5392, '2025-06-14 14:01:52', 0, 3.52119, 3.56622, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(66, 'BNBUSDT', 'BUY', 0.833333, 710, '2025-06-14 14:01:57', 0, 674.5, 781, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(67, 'XRPUSDT', 'BUY', 0.833333, 3.5392, '2025-06-14 14:02:10', 0, 3.52119, 3.56622, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(68, 'BNBUSDT', 'BUY', 0.833333, 710, '2025-06-14 14:02:23', 0, 674.5, 781, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(69, 'XRPUSDT', 'BUY', 0.833333, 3.5392, '2025-06-14 14:02:40', 0, 3.52119, 3.56622, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL),
(70, 'BNBUSDT', 'BUY', 0.833333, 710, '2025-06-14 14:02:45', 0, 674.5, 781, 'safe_multi_indicator', 'MACD: Бычье пересечение; EMA: Восходящий тренд; ADX: Сильный восходящий тренд', NULL, NULL);

-- --------------------------------------------------------

--
-- Структура таблицы `trades`
--

CREATE TABLE `trades` (
  `id` int NOT NULL,
  `symbol` varchar(20) NOT NULL,
  `side` varchar(10) NOT NULL,
  `entry_price` float NOT NULL,
  `exit_price` float DEFAULT NULL,
  `quantity` float NOT NULL,
  `profit` float DEFAULT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'OPEN',
  `strategy` varchar(50) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `closed_at` timestamp NULL DEFAULT NULL,
  `stop_loss` float DEFAULT NULL,
  `take_profit` float DEFAULT NULL,
  `profit_percent` float DEFAULT NULL,
  `trailing_stop` tinyint(1) DEFAULT '0',
  `commission` float DEFAULT '0',
  `notes` text,
  `user_id` int DEFAULT NULL COMMENT 'ID пользователя (может быть NULL для старых записей)'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Структура таблицы `trading_pairs`
--

CREATE TABLE `trading_pairs` (
  `id` int NOT NULL,
  `symbol` varchar(20) NOT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `min_position_size` float DEFAULT NULL,
  `max_position_size` float DEFAULT NULL,
  `strategy` varchar(50) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `stop_loss_percent` float DEFAULT '2',
  `take_profit_percent` float DEFAULT '4',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Дамп данных таблицы `trading_pairs`
--

INSERT INTO `trading_pairs` (`id`, `symbol`, `is_active`, `min_position_size`, `max_position_size`, `strategy`, `created_at`, `stop_loss_percent`, `take_profit_percent`, `updated_at`) VALUES
(1, 'BTCUSDT', 1, NULL, NULL, 'conservative', '2025-06-13 11:13:12', 1, 3, '2025-06-14 16:27:32'),
(2, 'ETHUSDT', 1, NULL, NULL, 'conservative', '2025-06-13 11:13:12', 1, 3, '2025-06-14 16:27:32'),
(3, 'BNBUSDT', 1, NULL, NULL, 'safe_multi_indicator', '2025-06-13 11:13:12', 1.5, 3, '2025-06-14 16:27:32'),
(4, 'SOLUSDT', 1, NULL, NULL, 'safe_multi_indicator', '2025-06-13 11:13:12', 1.5, 3, '2025-06-14 16:27:32'),
(5, 'ADAUSDT', 1, NULL, NULL, 'safe_multi_indicator', '2025-06-13 10:07:12', 1.5, 3, '2025-06-14 16:27:32'),
(6, 'DOGEUSDT', 1, NULL, NULL, 'safe_multi_indicator', '2025-06-13 10:07:12', 1.5, 3, '2025-06-14 16:27:32'),
(7, 'XRPUSDT', 1, NULL, NULL, 'safe_multi_indicator', '2025-06-13 10:07:12', 1.5, 3, '2025-06-14 16:27:32'),
(8, 'DOTUSDT', 1, NULL, NULL, 'safe_multi_indicator', '2025-06-13 10:07:12', 1.5, 3, '2025-06-14 16:27:32');

-- --------------------------------------------------------

--
-- Структура таблицы `users`
--

CREATE TABLE `users` (
  `id` int NOT NULL,
  `username` varchar(50) NOT NULL,
  `hashed_password` varchar(128) NOT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `is_blocked` tinyint(1) DEFAULT '0',
  `failed_login_attempts` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `last_login` timestamp NULL DEFAULT NULL,
  `blocked_at` timestamp NULL DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `is_admin` tinyint(1) DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Дамп данных таблицы `users`
--

INSERT INTO `users` (`id`, `username`, `hashed_password`, `is_active`, `is_blocked`, `failed_login_attempts`, `created_at`, `last_login`, `blocked_at`, `email`, `is_admin`) VALUES
(1, 'WaySenCryptoTop', '$2b$12$Hrv3wXuwXczSXwVOCUTG9.6523svqV8TWNG50qX4Fp9Pgb4Mml6oy', 1, 0, 0, '2025-06-13 08:21:55', '2025-06-14 08:38:20', NULL, NULL, 1);

--
-- Индексы сохранённых таблиц
--

--
-- Индексы таблицы `balances`
--
ALTER TABLE `balances`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_currency` (`currency`),
  ADD KEY `idx_timestamp` (`timestamp`),
  ADD KEY `idx_currency_timestamp` (`currency`,`timestamp`);

--
-- Индексы таблицы `bot_settings`
--
ALTER TABLE `bot_settings`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `key` (`key`),
  ADD KEY `idx_key` (`key`);

--
-- Индексы таблицы `bot_state`
--
ALTER TABLE `bot_state`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_updated_at` (`updated_at`);

--
-- Индексы таблицы `signals`
--
ALTER TABLE `signals`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_symbol` (`symbol`),
  ADD KEY `idx_created_at` (`created_at`),
  ADD KEY `idx_executed` (`executed`),
  ADD KEY `idx_strategy` (`strategy`);

--
-- Индексы таблицы `trades`
--
ALTER TABLE `trades`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_symbol` (`symbol`),
  ADD KEY `idx_status` (`status`),
  ADD KEY `idx_created_at` (`created_at`),
  ADD KEY `idx_closed_at` (`closed_at`),
  ADD KEY `user_id` (`user_id`);

--
-- Индексы таблицы `trading_pairs`
--
ALTER TABLE `trading_pairs`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `symbol` (`symbol`),
  ADD KEY `idx_symbol` (`symbol`);

--
-- Индексы таблицы `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD KEY `idx_username` (`username`);

--
-- AUTO_INCREMENT для сохранённых таблиц
--

--
-- AUTO_INCREMENT для таблицы `balances`
--
ALTER TABLE `balances`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=50;

--
-- AUTO_INCREMENT для таблицы `bot_settings`
--
ALTER TABLE `bot_settings`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `bot_state`
--
ALTER TABLE `bot_state`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT для таблицы `signals`
--
ALTER TABLE `signals`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=71;

--
-- AUTO_INCREMENT для таблицы `trades`
--
ALTER TABLE `trades`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT для таблицы `trading_pairs`
--
ALTER TABLE `trading_pairs`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT для таблицы `users`
--
ALTER TABLE `users`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Ограничения внешнего ключа сохраненных таблиц
--

--
-- Ограничения внешнего ключа таблицы `trades`
--
ALTER TABLE `trades`
  ADD CONSTRAINT `trades_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
