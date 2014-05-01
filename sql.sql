-- phpMyAdmin SQL Dump
-- version 4.1.9
-- http://www.phpmyadmin.net
--
-- Host: 127.0.0.1
-- Generation Time: May 01, 2014 at 03:59 PM
-- Server version: 5.6.16
-- PHP Version: 5.4.24

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `DupRSS`
--
CREATE DATABASE IF NOT EXISTS `DupRSS` DEFAULT CHARACTER SET latin1 COLLATE latin1_swedish_ci;
USE `DupRSS`;

-- --------------------------------------------------------

--
-- Table structure for table `Feeds_DupRSS`
--

DROP TABLE IF EXISTS `Feeds_DupRSS`;
CREATE TABLE IF NOT EXISTS `Feeds_DupRSS` (
  `Feed_id` int(11) NOT NULL AUTO_INCREMENT,
  `Feed_rssInfo` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_swedish_ci,
  `Feed_url` varchar(255) NOT NULL,
  `Feed_folder` varchar(255) NOT NULL,
  PRIMARY KEY (`Feed_id`),
  UNIQUE KEY `Feed_url` (`Feed_url`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=77 ;

-- --------------------------------------------------------

--
-- Table structure for table `Items_DupRSS`
--

DROP TABLE IF EXISTS `Items_DupRSS`;
CREATE TABLE IF NOT EXISTS `Items_DupRSS` (
  `Item_id` mediumint(9) NOT NULL AUTO_INCREMENT,
  `Item_xml` longtext CHARACTER SET utf8 NOT NULL,
  `Item_date` datetime DEFAULT CURRENT_TIMESTAMP,
  `Item_feed` mediumint(9) NOT NULL,
  `Item_title` varchar(500) CHARACTER SET utf8 NOT NULL,
  PRIMARY KEY (`Item_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=42 ;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
