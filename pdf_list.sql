/*
mysql
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for pdf_list
-- ----------------------------
DROP TABLE IF EXISTS `pdf_list`;
CREATE TABLE `pdf_list` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `cat` varchar(50) NOT NULL COMMENT '分类',
  `raw_id` varchar(50) NOT NULL DEFAULT '' COMMENT '初始ID',
  `version` int(10) NOT NULL DEFAULT '0' COMMENT '版本',
  `res_json` text NOT NULL COMMENT '返回atom结构转json写入',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
