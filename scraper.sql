-- phpMyAdmin SQL Dump
-- version 5.1.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Gegenereerd op: 02 jan 2022 om 18:24
-- Serverversie: 10.4.21-MariaDB
-- PHP-versie: 8.0.11

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `ltesmzpu_waze`
--

-- --------------------------------------------------------

--
-- Tabelstructuur voor tabel `scraper`
--

CREATE TABLE `scraper` (
  `ID` int(11) NOT NULL,
  `date` bigint(20) NOT NULL,
  `author` varchar(255) DEFAULT NULL,
  `text` longtext DEFAULT NULL,
  `href` varchar(255) NOT NULL,
  `story_fbid` varchar(254) NOT NULL,
  `fb_id` varchar(254) NOT NULL,
  `status` varchar(254) NOT NULL,
  `needed` varchar(254) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Indexen voor geëxporteerde tabellen
--

--
-- Indexen voor tabel `scraper`
--
ALTER TABLE `scraper`
  ADD PRIMARY KEY (`ID`);

--
-- AUTO_INCREMENT voor geëxporteerde tabellen
--

--
-- AUTO_INCREMENT voor een tabel `scraper`
--
ALTER TABLE `scraper`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
