# Copyright 2023 The MediaPipe Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""MediaPipe face landmarker task."""

import dataclasses
import enum
from typing import Callable, Mapping, Optional, List

import numpy as np

from mediapipe.framework.formats import classification_pb2
from mediapipe.framework.formats import landmark_pb2
from mediapipe.framework.formats import matrix_data_pb2
from mediapipe.python import packet_creator
from mediapipe.python import packet_getter
from mediapipe.python._framework_bindings import image as image_module
from mediapipe.python._framework_bindings import packet as packet_module
# pylint: disable=unused-import
from mediapipe.tasks.cc.vision.face_geometry.proto import face_geometry_pb2
# pylint: enable=unused-import
from mediapipe.tasks.cc.vision.face_landmarker.proto import face_landmarker_graph_options_pb2
from mediapipe.tasks.python.components.containers import category as category_module
from mediapipe.tasks.python.components.containers import landmark as landmark_module
from mediapipe.tasks.python.core import base_options as base_options_module
from mediapipe.tasks.python.core import task_info as task_info_module
from mediapipe.tasks.python.core.optional_dependencies import doc_controls
from mediapipe.tasks.python.vision.core import base_vision_task_api
from mediapipe.tasks.python.vision.core import image_processing_options as image_processing_options_module
from mediapipe.tasks.python.vision.core import vision_task_running_mode as running_mode_module

_BaseOptions = base_options_module.BaseOptions
_FaceLandmarkerGraphOptionsProto = (
    face_landmarker_graph_options_pb2.FaceLandmarkerGraphOptions
)
_LayoutEnum = matrix_data_pb2.MatrixData.Layout
_RunningMode = running_mode_module.VisionTaskRunningMode
_ImageProcessingOptions = image_processing_options_module.ImageProcessingOptions
_TaskInfo = task_info_module.TaskInfo

_IMAGE_IN_STREAM_NAME = 'image_in'
_IMAGE_OUT_STREAM_NAME = 'image_out'
_IMAGE_TAG = 'IMAGE'
_NORM_RECT_STREAM_NAME = 'norm_rect_in'
_NORM_RECT_TAG = 'NORM_RECT'
_NORM_LANDMARKS_STREAM_NAME = 'norm_landmarks'
_NORM_LANDMARKS_TAG = 'NORM_LANDMARKS'
_BLENDSHAPES_STREAM_NAME = 'blendshapes'
_BLENDSHAPES_TAG = 'BLENDSHAPES'
_FACE_GEOMETRY_STREAM_NAME = 'face_geometry'
_FACE_GEOMETRY_TAG = 'FACE_GEOMETRY'
_TASK_GRAPH_NAME = 'mediapipe.tasks.vision.face_landmarker.FaceLandmarkerGraph'
_MICRO_SECONDS_PER_MILLISECOND = 1000


class Blendshapes(enum.IntEnum):
  """The 52 blendshape coefficients."""

  NEUTRAL = 0
  BROW_DOWN_LEFT = 1
  BROW_DOWN_RIGHT = 2
  BROW_INNER_UP = 3
  BROW_OUTER_UP_LEFT = 4
  BROW_OUTER_UP_RIGHT = 5
  CHEEK_PUFF = 6
  CHEEK_SQUINT_LEFT = 7
  CHEEK_SQUINT_RIGHT = 8
  EYE_BLINK_LEFT = 9
  EYE_BLINK_RIGHT = 10
  EYE_LOOK_DOWN_LEFT = 11
  EYE_LOOK_DOWN_RIGHT = 12
  EYE_LOOK_IN_LEFT = 13
  EYE_LOOK_IN_RIGHT = 14
  EYE_LOOK_OUT_LEFT = 15
  EYE_LOOK_OUT_RIGHT = 16
  EYE_LOOK_UP_LEFT = 17
  EYE_LOOK_UP_RIGHT = 18
  EYE_SQUINT_LEFT = 19
  EYE_SQUINT_RIGHT = 20
  EYE_WIDE_LEFT = 21
  EYE_WIDE_RIGHT = 22
  JAW_FORWARD = 23
  JAW_LEFT = 24
  JAW_OPEN = 25
  JAW_RIGHT = 26
  MOUTH_CLOSE = 27
  MOUTH_DIMPLE_LEFT = 28
  MOUTH_DIMPLE_RIGHT = 29
  MOUTH_FROWN_LEFT = 30
  MOUTH_FROWN_RIGHT = 31
  MOUTH_FUNNEL = 32
  MOUTH_LEFT = 33
  MOUTH_LOWER_DOWN_LEFT = 34
  MOUTH_LOWER_DOWN_RIGHT = 35
  MOUTH_PRESS_LEFT = 36
  MOUTH_PRESS_RIGHT = 37
  MOUTH_PUCKER = 38
  MOUTH_RIGHT = 39
  MOUTH_ROLL_LOWER = 40
  MOUTH_ROLL_UPPER = 41
  MOUTH_SHRUG_LOWER = 42
  MOUTH_SHRUG_UPPER = 43
  MOUTH_SMILE_LEFT = 44
  MOUTH_SMILE_RIGHT = 45
  MOUTH_STRETCH_LEFT = 46
  MOUTH_STRETCH_RIGHT = 47
  MOUTH_UPPER_UP_LEFT = 48
  MOUTH_UPPER_UP_RIGHT = 49
  NOSE_SNEER_LEFT = 50
  NOSE_SNEER_RIGHT = 51


@dataclasses.dataclass
class Connection:
  start: int
  end: int


class FaceLandmarksConnections:
  FACE_LANDMARKS_LIPS: List[Connection] = [
    Connection(61, 146),  Connection(146, 91),  Connection(91, 181),
    Connection(181, 84),  Connection(84, 17),   Connection(17, 314),
    Connection(314, 405), Connection(405, 321), Connection(321, 375),
    Connection(375, 291), Connection(61, 185),  Connection(185, 40),
    Connection(40, 39),   Connection(39, 37),   Connection(37, 0),
    Connection(0, 267),   Connection(267, 269), Connection(269, 270),
    Connection(270, 409), Connection(409, 291), Connection(78, 95),
    Connection(95, 88),   Connection(88, 178),  Connection(178, 87),
    Connection(87, 14),   Connection(14, 317),  Connection(317, 402),
    Connection(402, 318), Connection(318, 324), Connection(324, 308),
    Connection(78, 191),  Connection(191, 80),  Connection(80, 81),
    Connection(81, 82),   Connection(82, 13),   Connection(13, 312),
    Connection(312, 311), Connection(311, 310), Connection(310, 415),
    Connection(415, 308)
  ];

  FACE_LANDMARKS_LEFT_EYE: List[Connection] = [
    Connection(263, 249), Connection(249, 390), Connection(390, 373),
    Connection(373, 374), Connection(374, 380), Connection(380, 381),
    Connection(381, 382), Connection(382, 362), Connection(263, 466),
    Connection(466, 388), Connection(388, 387), Connection(387, 386),
    Connection(386, 385), Connection(385, 384), Connection(384, 398),
    Connection(398, 362)
  ];

  FACE_LANDMARKS_LEFT_EYEBROW: List[Connection] = [
    Connection(276, 283), Connection(283, 282), Connection(282, 295),
    Connection(295, 285), Connection(300, 293), Connection(293, 334),
    Connection(334, 296), Connection(296, 336)
  ];

  FACE_LANDMARKS_LEFT_IRIS: List[Connection] = [
    Connection(474, 475), Connection(475, 476), Connection(476, 477),
    Connection(477, 474)
  ];

  FACE_LANDMARKS_RIGHT_EYE: List[Connection] = [
    Connection(33, 7), Connection(7, 163), Connection(163, 144),
    Connection(144, 145), Connection(145, 153), Connection(153, 154),
    Connection(154, 155), Connection(155, 133), Connection(33, 246),
    Connection(246, 161), Connection(161, 160), Connection(160, 159),
    Connection(159, 158), Connection(158, 157), Connection(157, 173),
    Connection(173, 133)
  ];

  FACE_LANDMARKS_RIGHT_EYEBROW: List[Connection] = [
    Connection(46, 53), Connection(53, 52), Connection(52, 65),
    Connection(65, 55), Connection(70, 63), Connection(63, 105),
    Connection(105, 66), Connection(66, 107)
  ];

  FACE_LANDMARKS_RIGHT_IRIS: List[Connection] = [
    Connection(469, 470), Connection(470, 471), Connection(471, 472),
    Connection(472, 469)
  ];

  FACE_LANDMARKS_FACE_OVAL: List[Connection] = [
    Connection(10, 338),  Connection(338, 297), Connection(297, 332),
    Connection(332, 284), Connection(284, 251), Connection(251, 389),
    Connection(389, 356), Connection(356, 454), Connection(454, 323),
    Connection(323, 361), Connection(361, 288), Connection(288, 397),
    Connection(397, 365), Connection(365, 379), Connection(379, 378),
    Connection(378, 400), Connection(400, 377), Connection(377, 152),
    Connection(152, 148), Connection(148, 176), Connection(176, 149),
    Connection(149, 150), Connection(150, 136), Connection(136, 172),
    Connection(172, 58),  Connection(58, 132),  Connection(132, 93),
    Connection(93, 234),  Connection(234, 127), Connection(127, 162),
    Connection(162, 21),  Connection(21, 54),   Connection(54, 103),
    Connection(103, 67),  Connection(67, 109),  Connection(109, 10)
  ];

  FACE_LANDMARKS_CONTOURS: List[Connection] = (
      FACE_LANDMARKS_LIPS
      + FACE_LANDMARKS_LEFT_EYE
      + FACE_LANDMARKS_LEFT_EYEBROW
      + FACE_LANDMARKS_RIGHT_EYE
      + FACE_LANDMARKS_RIGHT_EYEBROW
      + FACE_LANDMARKS_FACE_OVAL
  )

  FACE_LANDMARKS_TESSELATION: List[Connection]> = [
    Connection(127, 34),  Connection(34, 139),  Connection(139, 127),
    Connection(11, 0),    Connection(0, 37),    Connection(37, 11),
    Connection(232, 231), Connection(231, 120), Connection(120, 232),
    Connection(72, 37),   Connection(37, 39),   Connection(39, 72),
    Connection(128, 121), Connection(121, 47),  Connection(47, 128),
    Connection(232, 121), Connection(121, 128), Connection(128, 232),
    Connection(104, 69),  Connection(69, 67),   Connection(67, 104),
    Connection(175, 171), Connection(171, 148), Connection(148, 175),
    Connection(118, 50),  Connection(50, 101),  Connection(101, 118),
    Connection(73, 39),   Connection(39, 40),   Connection(40, 73),
    Connection(9, 151),   Connection(151, 108), Connection(108, 9),
    Connection(48, 115),  Connection(115, 131), Connection(131, 48),
    Connection(194, 204), Connection(204, 211), Connection(211, 194),
    Connection(74, 40),   Connection(40, 185),  Connection(185, 74),
    Connection(80, 42),   Connection(42, 183),  Connection(183, 80),
    Connection(40, 92),   Connection(92, 186),  Connection(186, 40),
    Connection(230, 229), Connection(229, 118), Connection(118, 230),
    Connection(202, 212), Connection(212, 214), Connection(214, 202),
    Connection(83, 18),   Connection(18, 17),   Connection(17, 83),
    Connection(76, 61),   Connection(61, 146),  Connection(146, 76),
    Connection(160, 29),  Connection(29, 30),   Connection(30, 160),
    Connection(56, 157),  Connection(157, 173), Connection(173, 56),
    Connection(106, 204), Connection(204, 194), Connection(194, 106),
    Connection(135, 214), Connection(214, 192), Connection(192, 135),
    Connection(203, 165), Connection(165, 98),  Connection(98, 203),
    Connection(21, 71),   Connection(71, 68),   Connection(68, 21),
    Connection(51, 45),   Connection(45, 4),    Connection(4, 51),
    Connection(144, 24),  Connection(24, 23),   Connection(23, 144),
    Connection(77, 146),  Connection(146, 91),  Connection(91, 77),
    Connection(205, 50),  Connection(50, 187),  Connection(187, 205),
    Connection(201, 200), Connection(200, 18),  Connection(18, 201),
    Connection(91, 106),  Connection(106, 182), Connection(182, 91),
    Connection(90, 91),   Connection(91, 181),  Connection(181, 90),
    Connection(85, 84),   Connection(84, 17),   Connection(17, 85),
    Connection(206, 203), Connection(203, 36),  Connection(36, 206),
    Connection(148, 171), Connection(171, 140), Connection(140, 148),
    Connection(92, 40),   Connection(40, 39),   Connection(39, 92),
    Connection(193, 189), Connection(189, 244), Connection(244, 193),
    Connection(159, 158), Connection(158, 28),  Connection(28, 159),
    Connection(247, 246), Connection(246, 161), Connection(161, 247),
    Connection(236, 3),   Connection(3, 196),   Connection(196, 236),
    Connection(54, 68),   Connection(68, 104),  Connection(104, 54),
    Connection(193, 168), Connection(168, 8),   Connection(8, 193),
    Connection(117, 228), Connection(228, 31),  Connection(31, 117),
    Connection(189, 193), Connection(193, 55),  Connection(55, 189),
    Connection(98, 97),   Connection(97, 99),   Connection(99, 98),
    Connection(126, 47),  Connection(47, 100),  Connection(100, 126),
    Connection(166, 79),  Connection(79, 218),  Connection(218, 166),
    Connection(155, 154), Connection(154, 26),  Connection(26, 155),
    Connection(209, 49),  Connection(49, 131),  Connection(131, 209),
    Connection(135, 136), Connection(136, 150), Connection(150, 135),
    Connection(47, 126),  Connection(126, 217), Connection(217, 47),
    Connection(223, 52),  Connection(52, 53),   Connection(53, 223),
    Connection(45, 51),   Connection(51, 134),  Connection(134, 45),
    Connection(211, 170), Connection(170, 140), Connection(140, 211),
    Connection(67, 69),   Connection(69, 108),  Connection(108, 67),
    Connection(43, 106),  Connection(106, 91),  Connection(91, 43),
    Connection(230, 119), Connection(119, 120), Connection(120, 230),
    Connection(226, 130), Connection(130, 247), Connection(247, 226),
    Connection(63, 53),   Connection(53, 52),   Connection(52, 63),
    Connection(238, 20),  Connection(20, 242),  Connection(242, 238),
    Connection(46, 70),   Connection(70, 156),  Connection(156, 46),
    Connection(78, 62),   Connection(62, 96),   Connection(96, 78),
    Connection(46, 53),   Connection(53, 63),   Connection(63, 46),
    Connection(143, 34),  Connection(34, 227),  Connection(227, 143),
    Connection(123, 117), Connection(117, 111), Connection(111, 123),
    Connection(44, 125),  Connection(125, 19),  Connection(19, 44),
    Connection(236, 134), Connection(134, 51),  Connection(51, 236),
    Connection(216, 206), Connection(206, 205), Connection(205, 216),
    Connection(154, 153), Connection(153, 22),  Connection(22, 154),
    Connection(39, 37),   Connection(37, 167),  Connection(167, 39),
    Connection(200, 201), Connection(201, 208), Connection(208, 200),
    Connection(36, 142),  Connection(142, 100), Connection(100, 36),
    Connection(57, 212),  Connection(212, 202), Connection(202, 57),
    Connection(20, 60),   Connection(60, 99),   Connection(99, 20),
    Connection(28, 158),  Connection(158, 157), Connection(157, 28),
    Connection(35, 226),  Connection(226, 113), Connection(113, 35),
    Connection(160, 159), Connection(159, 27),  Connection(27, 160),
    Connection(204, 202), Connection(202, 210), Connection(210, 204),
    Connection(113, 225), Connection(225, 46),  Connection(46, 113),
    Connection(43, 202),  Connection(202, 204), Connection(204, 43),
    Connection(62, 76),   Connection(76, 77),   Connection(77, 62),
    Connection(137, 123), Connection(123, 116), Connection(116, 137),
    Connection(41, 38),   Connection(38, 72),   Connection(72, 41),
    Connection(203, 129), Connection(129, 142), Connection(142, 203),
    Connection(64, 98),   Connection(98, 240),  Connection(240, 64),
    Connection(49, 102),  Connection(102, 64),  Connection(64, 49),
    Connection(41, 73),   Connection(73, 74),   Connection(74, 41),
    Connection(212, 216), Connection(216, 207), Connection(207, 212),
    Connection(42, 74),   Connection(74, 184),  Connection(184, 42),
    Connection(169, 170), Connection(170, 211), Connection(211, 169),
    Connection(170, 149), Connection(149, 176), Connection(176, 170),
    Connection(105, 66),  Connection(66, 69),   Connection(69, 105),
    Connection(122, 6),   Connection(6, 168),   Connection(168, 122),
    Connection(123, 147), Connection(147, 187), Connection(187, 123),
    Connection(96, 77),   Connection(77, 90),   Connection(90, 96),
    Connection(65, 55),   Connection(55, 107),  Connection(107, 65),
    Connection(89, 90),   Connection(90, 180),  Connection(180, 89),
    Connection(101, 100), Connection(100, 120), Connection(120, 101),
    Connection(63, 105),  Connection(105, 104), Connection(104, 63),
    Connection(93, 137),  Connection(137, 227), Connection(227, 93),
    Connection(15, 86),   Connection(86, 85),   Connection(85, 15),
    Connection(129, 102), Connection(102, 49),  Connection(49, 129),
    Connection(14, 87),   Connection(87, 86),   Connection(86, 14),
    Connection(55, 8),    Connection(8, 9),     Connection(9, 55),
    Connection(100, 47),  Connection(47, 121),  Connection(121, 100),
    Connection(145, 23),  Connection(23, 22),   Connection(22, 145),
    Connection(88, 89),   Connection(89, 179),  Connection(179, 88),
    Connection(6, 122),   Connection(122, 196), Connection(196, 6),
    Connection(88, 95),   Connection(95, 96),   Connection(96, 88),
    Connection(138, 172), Connection(172, 136), Connection(136, 138),
    Connection(215, 58),  Connection(58, 172),  Connection(172, 215),
    Connection(115, 48),  Connection(48, 219),  Connection(219, 115),
    Connection(42, 80),   Connection(80, 81),   Connection(81, 42),
    Connection(195, 3),   Connection(3, 51),    Connection(51, 195),
    Connection(43, 146),  Connection(146, 61),  Connection(61, 43),
    Connection(171, 175), Connection(175, 199), Connection(199, 171),
    Connection(81, 82),   Connection(82, 38),   Connection(38, 81),
    Connection(53, 46),   Connection(46, 225),  Connection(225, 53),
    Connection(144, 163), Connection(163, 110), Connection(110, 144),
    Connection(52, 65),   Connection(65, 66),   Connection(66, 52),
    Connection(229, 228), Connection(228, 117), Connection(117, 229),
    Connection(34, 127),  Connection(127, 234), Connection(234, 34),
    Connection(107, 108), Connection(108, 69),  Connection(69, 107),
    Connection(109, 108), Connection(108, 151), Connection(151, 109),
    Connection(48, 64),   Connection(64, 235),  Connection(235, 48),
    Connection(62, 78),   Connection(78, 191),  Connection(191, 62),
    Connection(129, 209), Connection(209, 126), Connection(126, 129),
    Connection(111, 35),  Connection(35, 143),  Connection(143, 111),
    Connection(117, 123), Connection(123, 50),  Connection(50, 117),
    Connection(222, 65),  Connection(65, 52),   Connection(52, 222),
    Connection(19, 125),  Connection(125, 141), Connection(141, 19),
    Connection(221, 55),  Connection(55, 65),   Connection(65, 221),
    Connection(3, 195),   Connection(195, 197), Connection(197, 3),
    Connection(25, 7),    Connection(7, 33),    Connection(33, 25),
    Connection(220, 237), Connection(237, 44),  Connection(44, 220),
    Connection(70, 71),   Connection(71, 139),  Connection(139, 70),
    Connection(122, 193), Connection(193, 245), Connection(245, 122),
    Connection(247, 130), Connection(130, 33),  Connection(33, 247),
    Connection(71, 21),   Connection(21, 162),  Connection(162, 71),
    Connection(170, 169), Connection(169, 150), Connection(150, 170),
    Connection(188, 174), Connection(174, 196), Connection(196, 188),
    Connection(216, 186), Connection(186, 92),  Connection(92, 216),
    Connection(2, 97),    Connection(97, 167),  Connection(167, 2),
    Connection(141, 125), Connection(125, 241), Connection(241, 141),
    Connection(164, 167), Connection(167, 37),  Connection(37, 164),
    Connection(72, 38),   Connection(38, 12),   Connection(12, 72),
    Connection(38, 82),   Connection(82, 13),   Connection(13, 38),
    Connection(63, 68),   Connection(68, 71),   Connection(71, 63),
    Connection(226, 35),  Connection(35, 111),  Connection(111, 226),
    Connection(101, 50),  Connection(50, 205),  Connection(205, 101),
    Connection(206, 92),  Connection(92, 165),  Connection(165, 206),
    Connection(209, 198), Connection(198, 217), Connection(217, 209),
    Connection(165, 167), Connection(167, 97),  Connection(97, 165),
    Connection(220, 115), Connection(115, 218), Connection(218, 220),
    Connection(133, 112), Connection(112, 243), Connection(243, 133),
    Connection(239, 238), Connection(238, 241), Connection(241, 239),
    Connection(214, 135), Connection(135, 169), Connection(169, 214),
    Connection(190, 173), Connection(173, 133), Connection(133, 190),
    Connection(171, 208), Connection(208, 32),  Connection(32, 171),
    Connection(125, 44),  Connection(44, 237),  Connection(237, 125),
    Connection(86, 87),   Connection(87, 178),  Connection(178, 86),
    Connection(85, 86),   Connection(86, 179),  Connection(179, 85),
    Connection(84, 85),   Connection(85, 180),  Connection(180, 84),
    Connection(83, 84),   Connection(84, 181),  Connection(181, 83),
    Connection(201, 83),  Connection(83, 182),  Connection(182, 201),
    Connection(137, 93),  Connection(93, 132),  Connection(132, 137),
    Connection(76, 62),   Connection(62, 183),  Connection(183, 76),
    Connection(61, 76),   Connection(76, 184),  Connection(184, 61),
    Connection(57, 61),   Connection(61, 185),  Connection(185, 57),
    Connection(212, 57),  Connection(57, 186),  Connection(186, 212),
    Connection(214, 207), Connection(207, 187), Connection(187, 214),
    Connection(34, 143),  Connection(143, 156), Connection(156, 34),
    Connection(79, 239),  Connection(239, 237), Connection(237, 79),
    Connection(123, 137), Connection(137, 177), Connection(177, 123),
    Connection(44, 1),    Connection(1, 4),     Connection(4, 44),
    Connection(201, 194), Connection(194, 32),  Connection(32, 201),
    Connection(64, 102),  Connection(102, 129), Connection(129, 64),
    Connection(213, 215), Connection(215, 138), Connection(138, 213),
    Connection(59, 166),  Connection(166, 219), Connection(219, 59),
    Connection(242, 99),  Connection(99, 97),   Connection(97, 242),
    Connection(2, 94),    Connection(94, 141),  Connection(141, 2),
    Connection(75, 59),   Connection(59, 235),  Connection(235, 75),
    Connection(24, 110),  Connection(110, 228), Connection(228, 24),
    Connection(25, 130),  Connection(130, 226), Connection(226, 25),
    Connection(23, 24),   Connection(24, 229),  Connection(229, 23),
    Connection(22, 23),   Connection(23, 230),  Connection(230, 22),
    Connection(26, 22),   Connection(22, 231),  Connection(231, 26),
    Connection(112, 26),  Connection(26, 232),  Connection(232, 112),
    Connection(189, 190), Connection(190, 243), Connection(243, 189),
    Connection(221, 56),  Connection(56, 190),  Connection(190, 221),
    Connection(28, 56),   Connection(56, 221),  Connection(221, 28),
    Connection(27, 28),   Connection(28, 222),  Connection(222, 27),
    Connection(29, 27),   Connection(27, 223),  Connection(223, 29),
    Connection(30, 29),   Connection(29, 224),  Connection(224, 30),
    Connection(247, 30),  Connection(30, 225),  Connection(225, 247),
    Connection(238, 79),  Connection(79, 20),   Connection(20, 238),
    Connection(166, 59),  Connection(59, 75),   Connection(75, 166),
    Connection(60, 75),   Connection(75, 240),  Connection(240, 60),
    Connection(147, 177), Connection(177, 215), Connection(215, 147),
    Connection(20, 79),   Connection(79, 166),  Connection(166, 20),
    Connection(187, 147), Connection(147, 213), Connection(213, 187),
    Connection(112, 233), Connection(233, 244), Connection(244, 112),
    Connection(233, 128), Connection(128, 245), Connection(245, 233),
    Connection(128, 114), Connection(114, 188), Connection(188, 128),
    Connection(114, 217), Connection(217, 174), Connection(174, 114),
    Connection(131, 115), Connection(115, 220), Connection(220, 131),
    Connection(217, 198), Connection(198, 236), Connection(236, 217),
    Connection(198, 131), Connection(131, 134), Connection(134, 198),
    Connection(177, 132), Connection(132, 58),  Connection(58, 177),
    Connection(143, 35),  Connection(35, 124),  Connection(124, 143),
    Connection(110, 163), Connection(163, 7),   Connection(7, 110),
    Connection(228, 110), Connection(110, 25),  Connection(25, 228),
    Connection(356, 389), Connection(389, 368), Connection(368, 356),
    Connection(11, 302),  Connection(302, 267), Connection(267, 11),
    Connection(452, 350), Connection(350, 349), Connection(349, 452),
    Connection(302, 303), Connection(303, 269), Connection(269, 302),
    Connection(357, 343), Connection(343, 277), Connection(277, 357),
    Connection(452, 453), Connection(453, 357), Connection(357, 452),
    Connection(333, 332), Connection(332, 297), Connection(297, 333),
    Connection(175, 152), Connection(152, 377), Connection(377, 175),
    Connection(347, 348), Connection(348, 330), Connection(330, 347),
    Connection(303, 304), Connection(304, 270), Connection(270, 303),
    Connection(9, 336),   Connection(336, 337), Connection(337, 9),
    Connection(278, 279), Connection(279, 360), Connection(360, 278),
    Connection(418, 262), Connection(262, 431), Connection(431, 418),
    Connection(304, 408), Connection(408, 409), Connection(409, 304),
    Connection(310, 415), Connection(415, 407), Connection(407, 310),
    Connection(270, 409), Connection(409, 410), Connection(410, 270),
    Connection(450, 348), Connection(348, 347), Connection(347, 450),
    Connection(422, 430), Connection(430, 434), Connection(434, 422),
    Connection(313, 314), Connection(314, 17),  Connection(17, 313),
    Connection(306, 307), Connection(307, 375), Connection(375, 306),
    Connection(387, 388), Connection(388, 260), Connection(260, 387),
    Connection(286, 414), Connection(414, 398), Connection(398, 286),
    Connection(335, 406), Connection(406, 418), Connection(418, 335),
    Connection(364, 367), Connection(367, 416), Connection(416, 364),
    Connection(423, 358), Connection(358, 327), Connection(327, 423),
    Connection(251, 284), Connection(284, 298), Connection(298, 251),
    Connection(281, 5),   Connection(5, 4),     Connection(4, 281),
    Connection(373, 374), Connection(374, 253), Connection(253, 373),
    Connection(307, 320), Connection(320, 321), Connection(321, 307),
    Connection(425, 427), Connection(427, 411), Connection(411, 425),
    Connection(421, 313), Connection(313, 18),  Connection(18, 421),
    Connection(321, 405), Connection(405, 406), Connection(406, 321),
    Connection(320, 404), Connection(404, 405), Connection(405, 320),
    Connection(315, 16),  Connection(16, 17),   Connection(17, 315),
    Connection(426, 425), Connection(425, 266), Connection(266, 426),
    Connection(377, 400), Connection(400, 369), Connection(369, 377),
    Connection(322, 391), Connection(391, 269), Connection(269, 322),
    Connection(417, 465), Connection(465, 464), Connection(464, 417),
    Connection(386, 257), Connection(257, 258), Connection(258, 386),
    Connection(466, 260), Connection(260, 388), Connection(388, 466),
    Connection(456, 399), Connection(399, 419), Connection(419, 456),
    Connection(284, 332), Connection(332, 333), Connection(333, 284),
    Connection(417, 285), Connection(285, 8),   Connection(8, 417),
    Connection(346, 340), Connection(340, 261), Connection(261, 346),
    Connection(413, 441), Connection(441, 285), Connection(285, 413),
    Connection(327, 460), Connection(460, 328), Connection(328, 327),
    Connection(355, 371), Connection(371, 329), Connection(329, 355),
    Connection(392, 439), Connection(439, 438), Connection(438, 392),
    Connection(382, 341), Connection(341, 256), Connection(256, 382),
    Connection(429, 420), Connection(420, 360), Connection(360, 429),
    Connection(364, 394), Connection(394, 379), Connection(379, 364),
    Connection(277, 343), Connection(343, 437), Connection(437, 277),
    Connection(443, 444), Connection(444, 283), Connection(283, 443),
    Connection(275, 440), Connection(440, 363), Connection(363, 275),
    Connection(431, 262), Connection(262, 369), Connection(369, 431),
    Connection(297, 338), Connection(338, 337), Connection(337, 297),
    Connection(273, 375), Connection(375, 321), Connection(321, 273),
    Connection(450, 451), Connection(451, 349), Connection(349, 450),
    Connection(446, 342), Connection(342, 467), Connection(467, 446),
    Connection(293, 334), Connection(334, 282), Connection(282, 293),
    Connection(458, 461), Connection(461, 462), Connection(462, 458),
    Connection(276, 353), Connection(353, 383), Connection(383, 276),
    Connection(308, 324), Connection(324, 325), Connection(325, 308),
    Connection(276, 300), Connection(300, 293), Connection(293, 276),
    Connection(372, 345), Connection(345, 447), Connection(447, 372),
    Connection(352, 345), Connection(345, 340), Connection(340, 352),
    Connection(274, 1),   Connection(1, 19),    Connection(19, 274),
    Connection(456, 248), Connection(248, 281), Connection(281, 456),
    Connection(436, 427), Connection(427, 425), Connection(425, 436),
    Connection(381, 256), Connection(256, 252), Connection(252, 381),
    Connection(269, 391), Connection(391, 393), Connection(393, 269),
    Connection(200, 199), Connection(199, 428), Connection(428, 200),
    Connection(266, 330), Connection(330, 329), Connection(329, 266),
    Connection(287, 273), Connection(273, 422), Connection(422, 287),
    Connection(250, 462), Connection(462, 328), Connection(328, 250),
    Connection(258, 286), Connection(286, 384), Connection(384, 258),
    Connection(265, 353), Connection(353, 342), Connection(342, 265),
    Connection(387, 259), Connection(259, 257), Connection(257, 387),
    Connection(424, 431), Connection(431, 430), Connection(430, 424),
    Connection(342, 353), Connection(353, 276), Connection(276, 342),
    Connection(273, 335), Connection(335, 424), Connection(424, 273),
    Connection(292, 325), Connection(325, 307), Connection(307, 292),
    Connection(366, 447), Connection(447, 345), Connection(345, 366),
    Connection(271, 303), Connection(303, 302), Connection(302, 271),
    Connection(423, 266), Connection(266, 371), Connection(371, 423),
    Connection(294, 455), Connection(455, 460), Connection(460, 294),
    Connection(279, 278), Connection(278, 294), Connection(294, 279),
    Connection(271, 272), Connection(272, 304), Connection(304, 271),
    Connection(432, 434), Connection(434, 427), Connection(427, 432),
    Connection(272, 407), Connection(407, 408), Connection(408, 272),
    Connection(394, 430), Connection(430, 431), Connection(431, 394),
    Connection(395, 369), Connection(369, 400), Connection(400, 395),
    Connection(334, 333), Connection(333, 299), Connection(299, 334),
    Connection(351, 417), Connection(417, 168), Connection(168, 351),
    Connection(352, 280), Connection(280, 411), Connection(411, 352),
    Connection(325, 319), Connection(319, 320), Connection(320, 325),
    Connection(295, 296), Connection(296, 336), Connection(336, 295),
    Connection(319, 403), Connection(403, 404), Connection(404, 319),
    Connection(330, 348), Connection(348, 349), Connection(349, 330),
    Connection(293, 298), Connection(298, 333), Connection(333, 293),
    Connection(323, 454), Connection(454, 447), Connection(447, 323),
    Connection(15, 16),   Connection(16, 315),  Connection(315, 15),
    Connection(358, 429), Connection(429, 279), Connection(279, 358),
    Connection(14, 15),   Connection(15, 316),  Connection(316, 14),
    Connection(285, 336), Connection(336, 9),   Connection(9, 285),
    Connection(329, 349), Connection(349, 350), Connection(350, 329),
    Connection(374, 380), Connection(380, 252), Connection(252, 374),
    Connection(318, 402), Connection(402, 403), Connection(403, 318),
    Connection(6, 197),   Connection(197, 419), Connection(419, 6),
    Connection(318, 319), Connection(319, 325), Connection(325, 318),
    Connection(367, 364), Connection(364, 365), Connection(365, 367),
    Connection(435, 367), Connection(367, 397), Connection(397, 435),
    Connection(344, 438), Connection(438, 439), Connection(439, 344),
    Connection(272, 271), Connection(271, 311), Connection(311, 272),
    Connection(195, 5),   Connection(5, 281),   Connection(281, 195),
    Connection(273, 287), Connection(287, 291), Connection(291, 273),
    Connection(396, 428), Connection(428, 199), Connection(199, 396),
    Connection(311, 271), Connection(271, 268), Connection(268, 311),
    Connection(283, 444), Connection(444, 445), Connection(445, 283),
    Connection(373, 254), Connection(254, 339), Connection(339, 373),
    Connection(282, 334), Connection(334, 296), Connection(296, 282),
    Connection(449, 347), Connection(347, 346), Connection(346, 449),
    Connection(264, 447), Connection(447, 454), Connection(454, 264),
    Connection(336, 296), Connection(296, 299), Connection(299, 336),
    Connection(338, 10),  Connection(10, 151),  Connection(151, 338),
    Connection(278, 439), Connection(439, 455), Connection(455, 278),
    Connection(292, 407), Connection(407, 415), Connection(415, 292),
    Connection(358, 371), Connection(371, 355), Connection(355, 358),
    Connection(340, 345), Connection(345, 372), Connection(372, 340),
    Connection(346, 347), Connection(347, 280), Connection(280, 346),
    Connection(442, 443), Connection(443, 282), Connection(282, 442),
    Connection(19, 94),   Connection(94, 370),  Connection(370, 19),
    Connection(441, 442), Connection(442, 295), Connection(295, 441),
    Connection(248, 419), Connection(419, 197), Connection(197, 248),
    Connection(263, 255), Connection(255, 359), Connection(359, 263),
    Connection(440, 275), Connection(275, 274), Connection(274, 440),
    Connection(300, 383), Connection(383, 368), Connection(368, 300),
    Connection(351, 412), Connection(412, 465), Connection(465, 351),
    Connection(263, 467), Connection(467, 466), Connection(466, 263),
    Connection(301, 368), Connection(368, 389), Connection(389, 301),
    Connection(395, 378), Connection(378, 379), Connection(379, 395),
    Connection(412, 351), Connection(351, 419), Connection(419, 412),
    Connection(436, 426), Connection(426, 322), Connection(322, 436),
    Connection(2, 164),   Connection(164, 393), Connection(393, 2),
    Connection(370, 462), Connection(462, 461), Connection(461, 370),
    Connection(164, 0),   Connection(0, 267),   Connection(267, 164),
    Connection(302, 11),  Connection(11, 12),   Connection(12, 302),
    Connection(268, 12),  Connection(12, 13),   Connection(13, 268),
    Connection(293, 300), Connection(300, 301), Connection(301, 293),
    Connection(446, 261), Connection(261, 340), Connection(340, 446),
    Connection(330, 266), Connection(266, 425), Connection(425, 330),
    Connection(426, 423), Connection(423, 391), Connection(391, 426),
    Connection(429, 355), Connection(355, 437), Connection(437, 429),
    Connection(391, 327), Connection(327, 326), Connection(326, 391),
    Connection(440, 457), Connection(457, 438), Connection(438, 440),
    Connection(341, 382), Connection(382, 362), Connection(362, 341),
    Connection(459, 457), Connection(457, 461), Connection(461, 459),
    Connection(434, 430), Connection(430, 394), Connection(394, 434),
    Connection(414, 463), Connection(463, 362), Connection(362, 414),
    Connection(396, 369), Connection(369, 262), Connection(262, 396),
    Connection(354, 461), Connection(461, 457), Connection(457, 354),
    Connection(316, 403), Connection(403, 402), Connection(402, 316),
    Connection(315, 404), Connection(404, 403), Connection(403, 315),
    Connection(314, 405), Connection(405, 404), Connection(404, 314),
    Connection(313, 406), Connection(406, 405), Connection(405, 313),
    Connection(421, 418), Connection(418, 406), Connection(406, 421),
    Connection(366, 401), Connection(401, 361), Connection(361, 366),
    Connection(306, 408), Connection(408, 407), Connection(407, 306),
    Connection(291, 409), Connection(409, 408), Connection(408, 291),
    Connection(287, 410), Connection(410, 409), Connection(409, 287),
    Connection(432, 436), Connection(436, 410), Connection(410, 432),
    Connection(434, 416), Connection(416, 411), Connection(411, 434),
    Connection(264, 368), Connection(368, 383), Connection(383, 264),
    Connection(309, 438), Connection(438, 457), Connection(457, 309),
    Connection(352, 376), Connection(376, 401), Connection(401, 352),
    Connection(274, 275), Connection(275, 4),   Connection(4, 274),
    Connection(421, 428), Connection(428, 262), Connection(262, 421),
    Connection(294, 327), Connection(327, 358), Connection(358, 294),
    Connection(433, 416), Connection(416, 367), Connection(367, 433),
    Connection(289, 455), Connection(455, 439), Connection(439, 289),
    Connection(462, 370), Connection(370, 326), Connection(326, 462),
    Connection(2, 326),   Connection(326, 370), Connection(370, 2),
    Connection(305, 460), Connection(460, 455), Connection(455, 305),
    Connection(254, 449), Connection(449, 448), Connection(448, 254),
    Connection(255, 261), Connection(261, 446), Connection(446, 255),
    Connection(253, 450), Connection(450, 449), Connection(449, 253),
    Connection(252, 451), Connection(451, 450), Connection(450, 252),
    Connection(256, 452), Connection(452, 451), Connection(451, 256),
    Connection(341, 453), Connection(453, 452), Connection(452, 341),
    Connection(413, 464), Connection(464, 463), Connection(463, 413),
    Connection(441, 413), Connection(413, 414), Connection(414, 441),
    Connection(258, 442), Connection(442, 441), Connection(441, 258),
    Connection(257, 443), Connection(443, 442), Connection(442, 257),
    Connection(259, 444), Connection(444, 443), Connection(443, 259),
    Connection(260, 445), Connection(445, 444), Connection(444, 260),
    Connection(467, 342), Connection(342, 445), Connection(445, 467),
    Connection(459, 458), Connection(458, 250), Connection(250, 459),
    Connection(289, 392), Connection(392, 290), Connection(290, 289),
    Connection(290, 328), Connection(328, 460), Connection(460, 290),
    Connection(376, 433), Connection(433, 435), Connection(435, 376),
    Connection(250, 290), Connection(290, 392), Connection(392, 250),
    Connection(411, 416), Connection(416, 433), Connection(433, 411),
    Connection(341, 463), Connection(463, 464), Connection(464, 341),
    Connection(453, 464), Connection(464, 465), Connection(465, 453),
    Connection(357, 465), Connection(465, 412), Connection(412, 357),
    Connection(343, 412), Connection(412, 399), Connection(399, 343),
    Connection(360, 363), Connection(363, 440), Connection(440, 360),
    Connection(437, 399), Connection(399, 456), Connection(456, 437),
    Connection(420, 456), Connection(456, 363), Connection(363, 420),
    Connection(401, 435), Connection(435, 288), Connection(288, 401),
    Connection(372, 383), Connection(383, 353), Connection(353, 372),
    Connection(339, 255), Connection(255, 249), Connection(249, 339),
    Connection(448, 261), Connection(261, 255), Connection(255, 448),
    Connection(133, 243), Connection(243, 190), Connection(190, 133),
    Connection(133, 155), Connection(155, 112), Connection(112, 133),
    Connection(33, 246),  Connection(246, 247), Connection(247, 33),
    Connection(33, 130),  Connection(130, 25),  Connection(25, 33),
    Connection(398, 384), Connection(384, 286), Connection(286, 398),
    Connection(362, 398), Connection(398, 414), Connection(414, 362),
    Connection(362, 463), Connection(463, 341), Connection(341, 362),
    Connection(263, 359), Connection(359, 467), Connection(467, 263),
    Connection(263, 249), Connection(249, 255), Connection(255, 263),
    Connection(466, 467), Connection(467, 260), Connection(260, 466),
    Connection(75, 60),   Connection(60, 166),  Connection(166, 75),
    Connection(238, 239), Connection(239, 79),  Connection(79, 238),
    Connection(162, 127), Connection(127, 139), Connection(139, 162),
    Connection(72, 11),   Connection(11, 37),   Connection(37, 72),
    Connection(121, 232), Connection(232, 120), Connection(120, 121),
    Connection(73, 72),   Connection(72, 39),   Connection(39, 73),
    Connection(114, 128), Connection(128, 47),  Connection(47, 114),
    Connection(233, 232), Connection(232, 128), Connection(128, 233),
    Connection(103, 104), Connection(104, 67),  Connection(67, 103),
    Connection(152, 175), Connection(175, 148), Connection(148, 152),
    Connection(119, 118), Connection(118, 101), Connection(101, 119),
    Connection(74, 73),   Connection(73, 40),   Connection(40, 74),
    Connection(107, 9),   Connection(9, 108),   Connection(108, 107),
    Connection(49, 48),   Connection(48, 131),  Connection(131, 49),
    Connection(32, 194),  Connection(194, 211), Connection(211, 32),
    Connection(184, 74),  Connection(74, 185),  Connection(185, 184),
    Connection(191, 80),  Connection(80, 183),  Connection(183, 191),
    Connection(185, 40),  Connection(40, 186),  Connection(186, 185),
    Connection(119, 230), Connection(230, 118), Connection(118, 119),
    Connection(210, 202), Connection(202, 214), Connection(214, 210),
    Connection(84, 83),   Connection(83, 17),   Connection(17, 84),
    Connection(77, 76),   Connection(76, 146),  Connection(146, 77),
    Connection(161, 160), Connection(160, 30),  Connection(30, 161),
    Connection(190, 56),  Connection(56, 173),  Connection(173, 190),
    Connection(182, 106), Connection(106, 194), Connection(194, 182),
    Connection(138, 135), Connection(135, 192), Connection(192, 138),
    Connection(129, 203), Connection(203, 98),  Connection(98, 129),
    Connection(54, 21),   Connection(21, 68),   Connection(68, 54),
    Connection(5, 51),    Connection(51, 4),    Connection(4, 5),
    Connection(145, 144), Connection(144, 23),  Connection(23, 145),
    Connection(90, 77),   Connection(77, 91),   Connection(91, 90),
    Connection(207, 205), Connection(205, 187), Connection(187, 207),
    Connection(83, 201),  Connection(201, 18),  Connection(18, 83),
    Connection(181, 91),  Connection(91, 182),  Connection(182, 181),
    Connection(180, 90),  Connection(90, 181),  Connection(181, 180),
    Connection(16, 85),   Connection(85, 17),   Connection(17, 16),
    Connection(205, 206), Connection(206, 36),  Connection(36, 205),
    Connection(176, 148), Connection(148, 140), Connection(140, 176),
    Connection(165, 92),  Connection(92, 39),   Connection(39, 165),
    Connection(245, 193), Connection(193, 244), Connection(244, 245),
    Connection(27, 159),  Connection(159, 28),  Connection(28, 27),
    Connection(30, 247),  Connection(247, 161), Connection(161, 30),
    Connection(174, 236), Connection(236, 196), Connection(196, 174),
    Connection(103, 54),  Connection(54, 104),  Connection(104, 103),
    Connection(55, 193),  Connection(193, 8),   Connection(8, 55),
    Connection(111, 117), Connection(117, 31),  Connection(31, 111),
    Connection(221, 189), Connection(189, 55),  Connection(55, 221),
    Connection(240, 98),  Connection(98, 99),   Connection(99, 240),
    Connection(142, 126), Connection(126, 100), Connection(100, 142),
    Connection(219, 166), Connection(166, 218), Connection(218, 219),
    Connection(112, 155), Connection(155, 26),  Connection(26, 112),
    Connection(198, 209), Connection(209, 131), Connection(131, 198),
    Connection(169, 135), Connection(135, 150), Connection(150, 169),
    Connection(114, 47),  Connection(47, 217),  Connection(217, 114),
    Connection(224, 223), Connection(223, 53),  Connection(53, 224),
    Connection(220, 45),  Connection(45, 134),  Connection(134, 220),
    Connection(32, 211),  Connection(211, 140), Connection(140, 32),
    Connection(109, 67),  Connection(67, 108),  Connection(108, 109),
    Connection(146, 43),  Connection(43, 91),   Connection(91, 146),
    Connection(231, 230), Connection(230, 120), Connection(120, 231),
    Connection(113, 226), Connection(226, 247), Connection(247, 113),
    Connection(105, 63),  Connection(63, 52),   Connection(52, 105),
    Connection(241, 238), Connection(238, 242), Connection(242, 241),
    Connection(124, 46),  Connection(46, 156),  Connection(156, 124),
    Connection(95, 78),   Connection(78, 96),   Connection(96, 95),
    Connection(70, 46),   Connection(46, 63),   Connection(63, 70),
    Connection(116, 143), Connection(143, 227), Connection(227, 116),
    Connection(116, 123), Connection(123, 111), Connection(111, 116),
    Connection(1, 44),    Connection(44, 19),   Connection(19, 1),
    Connection(3, 236),   Connection(236, 51),  Connection(51, 3),
    Connection(207, 216), Connection(216, 205), Connection(205, 207),
    Connection(26, 154),  Connection(154, 22),  Connection(22, 26),
    Connection(165, 39),  Connection(39, 167),  Connection(167, 165),
    Connection(199, 200), Connection(200, 208), Connection(208, 199),
    Connection(101, 36),  Connection(36, 100),  Connection(100, 101),
    Connection(43, 57),   Connection(57, 202),  Connection(202, 43),
    Connection(242, 20),  Connection(20, 99),   Connection(99, 242),
    Connection(56, 28),   Connection(28, 157),  Connection(157, 56),
    Connection(124, 35),  Connection(35, 113),  Connection(113, 124),
    Connection(29, 160),  Connection(160, 27),  Connection(27, 29),
    Connection(211, 204), Connection(204, 210), Connection(210, 211),
    Connection(124, 113), Connection(113, 46),  Connection(46, 124),
    Connection(106, 43),  Connection(43, 204),  Connection(204, 106),
    Connection(96, 62),   Connection(62, 77),   Connection(77, 96),
    Connection(227, 137), Connection(137, 116), Connection(116, 227),
    Connection(73, 41),   Connection(41, 72),   Connection(72, 73),
    Connection(36, 203),  Connection(203, 142), Connection(142, 36),
    Connection(235, 64),  Connection(64, 240),  Connection(240, 235),
    Connection(48, 49),   Connection(49, 64),   Connection(64, 48),
    Connection(42, 41),   Connection(41, 74),   Connection(74, 42),
    Connection(214, 212), Connection(212, 207), Connection(207, 214),
    Connection(183, 42),  Connection(42, 184),  Connection(184, 183),
    Connection(210, 169), Connection(169, 211), Connection(211, 210),
    Connection(140, 170), Connection(170, 176), Connection(176, 140),
    Connection(104, 105), Connection(105, 69),  Connection(69, 104),
    Connection(193, 122), Connection(122, 168), Connection(168, 193),
    Connection(50, 123),  Connection(123, 187), Connection(187, 50),
    Connection(89, 96),   Connection(96, 90),   Connection(90, 89),
    Connection(66, 65),   Connection(65, 107),  Connection(107, 66),
    Connection(179, 89),  Connection(89, 180),  Connection(180, 179),
    Connection(119, 101), Connection(101, 120), Connection(120, 119),
    Connection(68, 63),   Connection(63, 104),  Connection(104, 68),
    Connection(234, 93),  Connection(93, 227),  Connection(227, 234),
    Connection(16, 15),   Connection(15, 85),   Connection(85, 16),
    Connection(209, 129), Connection(129, 49),  Connection(49, 209),
    Connection(15, 14),   Connection(14, 86),   Connection(86, 15),
    Connection(107, 55),  Connection(55, 9),    Connection(9, 107),
    Connection(120, 100), Connection(100, 121), Connection(121, 120),
    Connection(153, 145), Connection(145, 22),  Connection(22, 153),
    Connection(178, 88),  Connection(88, 179),  Connection(179, 178),
    Connection(197, 6),   Connection(6, 196),   Connection(196, 197),
    Connection(89, 88),   Connection(88, 96),   Connection(96, 89),
    Connection(135, 138), Connection(138, 136), Connection(136, 135),
    Connection(138, 215), Connection(215, 172), Connection(172, 138),
    Connection(218, 115), Connection(115, 219), Connection(219, 218),
    Connection(41, 42),   Connection(42, 81),   Connection(81, 41),
    Connection(5, 195),   Connection(195, 51),  Connection(51, 5),
    Connection(57, 43),   Connection(43, 61),   Connection(61, 57),
    Connection(208, 171), Connection(171, 199), Connection(199, 208),
    Connection(41, 81),   Connection(81, 38),   Connection(38, 41),
    Connection(224, 53),  Connection(53, 225),  Connection(225, 224),
    Connection(24, 144),  Connection(144, 110), Connection(110, 24),
    Connection(105, 52),  Connection(52, 66),   Connection(66, 105),
    Connection(118, 229), Connection(229, 117), Connection(117, 118),
    Connection(227, 34),  Connection(34, 234),  Connection(234, 227),
    Connection(66, 107),  Connection(107, 69),  Connection(69, 66),
    Connection(10, 109),  Connection(109, 151), Connection(151, 10),
    Connection(219, 48),  Connection(48, 235),  Connection(235, 219),
    Connection(183, 62),  Connection(62, 191),  Connection(191, 183),
    Connection(142, 129), Connection(129, 126), Connection(126, 142),
    Connection(116, 111), Connection(111, 143), Connection(143, 116),
    Connection(118, 117), Connection(117, 50),  Connection(50, 118),
    Connection(223, 222), Connection(222, 52),  Connection(52, 223),
    Connection(94, 19),   Connection(19, 141),  Connection(141, 94),
    Connection(222, 221), Connection(221, 65),  Connection(65, 222),
    Connection(196, 3),   Connection(3, 197),   Connection(197, 196),
    Connection(45, 220),  Connection(220, 44),  Connection(44, 45),
    Connection(156, 70),  Connection(70, 139),  Connection(139, 156),
    Connection(188, 122), Connection(122, 245), Connection(245, 188),
    Connection(139, 71),  Connection(71, 162),  Connection(162, 139),
    Connection(149, 170), Connection(170, 150), Connection(150, 149),
    Connection(122, 188), Connection(188, 196), Connection(196, 122),
    Connection(206, 216), Connection(216, 92),  Connection(92, 206),
    Connection(164, 2),   Connection(2, 167),   Connection(167, 164),
    Connection(242, 141), Connection(141, 241), Connection(241, 242),
    Connection(0, 164),   Connection(164, 37),  Connection(37, 0),
    Connection(11, 72),   Connection(72, 12),   Connection(12, 11),
    Connection(12, 38),   Connection(38, 13),   Connection(13, 12),
    Connection(70, 63),   Connection(63, 71),   Connection(71, 70),
    Connection(31, 226),  Connection(226, 111), Connection(111, 31),
    Connection(36, 101),  Connection(101, 205), Connection(205, 36),
    Connection(203, 206), Connection(206, 165), Connection(165, 203),
    Connection(126, 209), Connection(209, 217), Connection(217, 126),
    Connection(98, 165),  Connection(165, 97),  Connection(97, 98),
    Connection(237, 220), Connection(220, 218), Connection(218, 237),
    Connection(237, 239), Connection(239, 241), Connection(241, 237),
    Connection(210, 214), Connection(214, 169), Connection(169, 210),
    Connection(140, 171), Connection(171, 32),  Connection(32, 140),
    Connection(241, 125), Connection(125, 237), Connection(237, 241),
    Connection(179, 86),  Connection(86, 178),  Connection(178, 179),
    Connection(180, 85),  Connection(85, 179),  Connection(179, 180),
    Connection(181, 84),  Connection(84, 180),  Connection(180, 181),
    Connection(182, 83),  Connection(83, 181),  Connection(181, 182),
    Connection(194, 201), Connection(201, 182), Connection(182, 194),
    Connection(177, 137), Connection(137, 132), Connection(132, 177),
    Connection(184, 76),  Connection(76, 183),  Connection(183, 184),
    Connection(185, 61),  Connection(61, 184),  Connection(184, 185),
    Connection(186, 57),  Connection(57, 185),  Connection(185, 186),
    Connection(216, 212), Connection(212, 186), Connection(186, 216),
    Connection(192, 214), Connection(214, 187), Connection(187, 192),
    Connection(139, 34),  Connection(34, 156),  Connection(156, 139),
    Connection(218, 79),  Connection(79, 237),  Connection(237, 218),
    Connection(147, 123), Connection(123, 177), Connection(177, 147),
    Connection(45, 44),   Connection(44, 4),    Connection(4, 45),
    Connection(208, 201), Connection(201, 32),  Connection(32, 208),
    Connection(98, 64),   Connection(64, 129),  Connection(129, 98),
    Connection(192, 213), Connection(213, 138), Connection(138, 192),
    Connection(235, 59),  Connection(59, 219),  Connection(219, 235),
    Connection(141, 242), Connection(242, 97),  Connection(97, 141),
    Connection(97, 2),    Connection(2, 141),   Connection(141, 97),
    Connection(240, 75),  Connection(75, 235),  Connection(235, 240),
    Connection(229, 24),  Connection(24, 228),  Connection(228, 229),
    Connection(31, 25),   Connection(25, 226),  Connection(226, 31),
    Connection(230, 23),  Connection(23, 229),  Connection(229, 230),
    Connection(231, 22),  Connection(22, 230),  Connection(230, 231),
    Connection(232, 26),  Connection(26, 231),  Connection(231, 232),
    Connection(233, 112), Connection(112, 232), Connection(232, 233),
    Connection(244, 189), Connection(189, 243), Connection(243, 244),
    Connection(189, 221), Connection(221, 190), Connection(190, 189),
    Connection(222, 28),  Connection(28, 221),  Connection(221, 222),
    Connection(223, 27),  Connection(27, 222),  Connection(222, 223),
    Connection(224, 29),  Connection(29, 223),  Connection(223, 224),
    Connection(225, 30),  Connection(30, 224),  Connection(224, 225),
    Connection(113, 247), Connection(247, 225), Connection(225, 113),
    Connection(99, 60),   Connection(60, 240),  Connection(240, 99),
    Connection(213, 147), Connection(147, 215), Connection(215, 213),
    Connection(60, 20),   Connection(20, 166),  Connection(166, 60),
    Connection(192, 187), Connection(187, 213), Connection(213, 192),
    Connection(243, 112), Connection(112, 244), Connection(244, 243),
    Connection(244, 233), Connection(233, 245), Connection(245, 244),
    Connection(245, 128), Connection(128, 188), Connection(188, 245),
    Connection(188, 114), Connection(114, 174), Connection(174, 188),
    Connection(134, 131), Connection(131, 220), Connection(220, 134),
    Connection(174, 217), Connection(217, 236), Connection(236, 174),
    Connection(236, 198), Connection(198, 134), Connection(134, 236),
    Connection(215, 177), Connection(177, 58),  Connection(58, 215),
    Connection(156, 143), Connection(143, 124), Connection(124, 156),
    Connection(25, 110),  Connection(110, 7),   Connection(7, 25),
    Connection(31, 228),  Connection(228, 25),  Connection(25, 31),
    Connection(264, 356), Connection(356, 368), Connection(368, 264),
    Connection(0, 11),    Connection(11, 267),  Connection(267, 0),
    Connection(451, 452), Connection(452, 349), Connection(349, 451),
    Connection(267, 302), Connection(302, 269), Connection(269, 267),
    Connection(350, 357), Connection(357, 277), Connection(277, 350),
    Connection(350, 452), Connection(452, 357), Connection(357, 350),
    Connection(299, 333), Connection(333, 297), Connection(297, 299),
    Connection(396, 175), Connection(175, 377), Connection(377, 396),
    Connection(280, 347), Connection(347, 330), Connection(330, 280),
    Connection(269, 303), Connection(303, 270), Connection(270, 269),
    Connection(151, 9),   Connection(9, 337),   Connection(337, 151),
    Connection(344, 278), Connection(278, 360), Connection(360, 344),
    Connection(424, 418), Connection(418, 431), Connection(431, 424),
    Connection(270, 304), Connection(304, 409), Connection(409, 270),
    Connection(272, 310), Connection(310, 407), Connection(407, 272),
    Connection(322, 270), Connection(270, 410), Connection(410, 322),
    Connection(449, 450), Connection(450, 347), Connection(347, 449),
    Connection(432, 422), Connection(422, 434), Connection(434, 432),
    Connection(18, 313),  Connection(313, 17),  Connection(17, 18),
    Connection(291, 306), Connection(306, 375), Connection(375, 291),
    Connection(259, 387), Connection(387, 260), Connection(260, 259),
    Connection(424, 335), Connection(335, 418), Connection(418, 424),
    Connection(434, 364), Connection(364, 416), Connection(416, 434),
    Connection(391, 423), Connection(423, 327), Connection(327, 391),
    Connection(301, 251), Connection(251, 298), Connection(298, 301),
    Connection(275, 281), Connection(281, 4),   Connection(4, 275),
    Connection(254, 373), Connection(373, 253), Connection(253, 254),
    Connection(375, 307), Connection(307, 321), Connection(321, 375),
    Connection(280, 425), Connection(425, 411), Connection(411, 280),
    Connection(200, 421), Connection(421, 18),  Connection(18, 200),
    Connection(335, 321), Connection(321, 406), Connection(406, 335),
    Connection(321, 320), Connection(320, 405), Connection(405, 321),
    Connection(314, 315), Connection(315, 17),  Connection(17, 314),
    Connection(423, 426), Connection(426, 266), Connection(266, 423),
    Connection(396, 377), Connection(377, 369), Connection(369, 396),
    Connection(270, 322), Connection(322, 269), Connection(269, 270),
    Connection(413, 417), Connection(417, 464), Connection(464, 413),
    Connection(385, 386), Connection(386, 258), Connection(258, 385),
    Connection(248, 456), Connection(456, 419), Connection(419, 248),
    Connection(298, 284), Connection(284, 333), Connection(333, 298),
    Connection(168, 417), Connection(417, 8),   Connection(8, 168),
    Connection(448, 346), Connection(346, 261), Connection(261, 448),
    Connection(417, 413), Connection(413, 285), Connection(285, 417),
    Connection(326, 327), Connection(327, 328), Connection(328, 326),
    Connection(277, 355), Connection(355, 329), Connection(329, 277),
    Connection(309, 392), Connection(392, 438), Connection(438, 309),
    Connection(381, 382), Connection(382, 256), Connection(256, 381),
    Connection(279, 429), Connection(429, 360), Connection(360, 279),
    Connection(365, 364), Connection(364, 379), Connection(379, 365),
    Connection(355, 277), Connection(277, 437), Connection(437, 355),
    Connection(282, 443), Connection(443, 283), Connection(283, 282),
    Connection(281, 275), Connection(275, 363), Connection(363, 281),
    Connection(395, 431), Connection(431, 369), Connection(369, 395),
    Connection(299, 297), Connection(297, 337), Connection(337, 299),
    Connection(335, 273), Connection(273, 321), Connection(321, 335),
    Connection(348, 450), Connection(450, 349), Connection(349, 348),
    Connection(359, 446), Connection(446, 467), Connection(467, 359),
    Connection(283, 293), Connection(293, 282), Connection(282, 283),
    Connection(250, 458), Connection(458, 462), Connection(462, 250),
    Connection(300, 276), Connection(276, 383), Connection(383, 300),
    Connection(292, 308), Connection(308, 325), Connection(325, 292),
    Connection(283, 276), Connection(276, 293), Connection(293, 283),
    Connection(264, 372), Connection(372, 447), Connection(447, 264),
    Connection(346, 352), Connection(352, 340), Connection(340, 346),
    Connection(354, 274), Connection(274, 19),  Connection(19, 354),
    Connection(363, 456), Connection(456, 281), Connection(281, 363),
    Connection(426, 436), Connection(436, 425), Connection(425, 426),
    Connection(380, 381), Connection(381, 252), Connection(252, 380),
    Connection(267, 269), Connection(269, 393), Connection(393, 267),
    Connection(421, 200), Connection(200, 428), Connection(428, 421),
    Connection(371, 266), Connection(266, 329), Connection(329, 371),
    Connection(432, 287), Connection(287, 422), Connection(422, 432),
    Connection(290, 250), Connection(250, 328), Connection(328, 290),
    Connection(385, 258), Connection(258, 384), Connection(384, 385),
    Connection(446, 265), Connection(265, 342), Connection(342, 446),
    Connection(386, 387), Connection(387, 257), Connection(257, 386),
    Connection(422, 424), Connection(424, 430), Connection(430, 422),
    Connection(445, 342), Connection(342, 276), Connection(276, 445),
    Connection(422, 273), Connection(273, 424), Connection(424, 422),
    Connection(306, 292), Connection(292, 307), Connection(307, 306),
    Connection(352, 366), Connection(366, 345), Connection(345, 352),
    Connection(268, 271), Connection(271, 302), Connection(302, 268),
    Connection(358, 423), Connection(423, 371), Connection(371, 358),
    Connection(327, 294), Connection(294, 460), Connection(460, 327),
    Connection(331, 279), Connection(279, 294), Connection(294, 331),
    Connection(303, 271), Connection(271, 304), Connection(304, 303),
    Connection(436, 432), Connection(432, 427), Connection(427, 436),
    Connection(304, 272), Connection(272, 408), Connection(408, 304),
    Connection(395, 394), Connection(394, 431), Connection(431, 395),
    Connection(378, 395), Connection(395, 400), Connection(400, 378),
    Connection(296, 334), Connection(334, 299), Connection(299, 296),
    Connection(6, 351),   Connection(351, 168), Connection(168, 6),
    Connection(376, 352), Connection(352, 411), Connection(411, 376),
    Connection(307, 325), Connection(325, 320), Connection(320, 307),
    Connection(285, 295), Connection(295, 336), Connection(336, 285),
    Connection(320, 319), Connection(319, 404), Connection(404, 320),
    Connection(329, 330), Connection(330, 349), Connection(349, 329),
    Connection(334, 293), Connection(293, 333), Connection(333, 334),
    Connection(366, 323), Connection(323, 447), Connection(447, 366),
    Connection(316, 15),  Connection(15, 315),  Connection(315, 316),
    Connection(331, 358), Connection(358, 279), Connection(279, 331),
    Connection(317, 14),  Connection(14, 316),  Connection(316, 317),
    Connection(8, 285),   Connection(285, 9),   Connection(9, 8),
    Connection(277, 329), Connection(329, 350), Connection(350, 277),
    Connection(253, 374), Connection(374, 252), Connection(252, 253),
    Connection(319, 318), Connection(318, 403), Connection(403, 319),
    Connection(351, 6),   Connection(6, 419),   Connection(419, 351),
    Connection(324, 318), Connection(318, 325), Connection(325, 324),
    Connection(397, 367), Connection(367, 365), Connection(365, 397),
    Connection(288, 435), Connection(435, 397), Connection(397, 288),
    Connection(278, 344), Connection(344, 439), Connection(439, 278),
    Connection(310, 272), Connection(272, 311), Connection(311, 310),
    Connection(248, 195), Connection(195, 281), Connection(281, 248),
    Connection(375, 273), Connection(273, 291), Connection(291, 375),
    Connection(175, 396), Connection(396, 199), Connection(199, 175),
    Connection(312, 311), Connection(311, 268), Connection(268, 312),
    Connection(276, 283), Connection(283, 445), Connection(445, 276),
    Connection(390, 373), Connection(373, 339), Connection(339, 390),
    Connection(295, 282), Connection(282, 296), Connection(296, 295),
    Connection(448, 449), Connection(449, 346), Connection(346, 448),
    Connection(356, 264), Connection(264, 454), Connection(454, 356),
    Connection(337, 336), Connection(336, 299), Connection(299, 337),
    Connection(337, 338), Connection(338, 151), Connection(151, 337),
    Connection(294, 278), Connection(278, 455), Connection(455, 294),
    Connection(308, 292), Connection(292, 415), Connection(415, 308),
    Connection(429, 358), Connection(358, 355), Connection(355, 429),
    Connection(265, 340), Connection(340, 372), Connection(372, 265),
    Connection(352, 346), Connection(346, 280), Connection(280, 352),
    Connection(295, 442), Connection(442, 282), Connection(282, 295),
    Connection(354, 19),  Connection(19, 370),  Connection(370, 354),
    Connection(285, 441), Connection(441, 295), Connection(295, 285),
    Connection(195, 248), Connection(248, 197), Connection(197, 195),
    Connection(457, 440), Connection(440, 274), Connection(274, 457),
    Connection(301, 300), Connection(300, 368), Connection(368, 301),
    Connection(417, 351), Connection(351, 465), Connection(465, 417),
    Connection(251, 301), Connection(301, 389), Connection(389, 251),
    Connection(394, 395), Connection(395, 379), Connection(379, 394),
    Connection(399, 412), Connection(412, 419), Connection(419, 399),
    Connection(410, 436), Connection(436, 322), Connection(322, 410),
    Connection(326, 2),   Connection(2, 393),   Connection(393, 326),
    Connection(354, 370), Connection(370, 461), Connection(461, 354),
    Connection(393, 164), Connection(164, 267), Connection(267, 393),
    Connection(268, 302), Connection(302, 12),  Connection(12, 268),
    Connection(312, 268), Connection(268, 13),  Connection(13, 312),
    Connection(298, 293), Connection(293, 301), Connection(301, 298),
    Connection(265, 446), Connection(446, 340), Connection(340, 265),
    Connection(280, 330), Connection(330, 425), Connection(425, 280),
    Connection(322, 426), Connection(426, 391), Connection(391, 322),
    Connection(420, 429), Connection(429, 437), Connection(437, 420),
    Connection(393, 391), Connection(391, 326), Connection(326, 393),
    Connection(344, 440), Connection(440, 438), Connection(438, 344),
    Connection(458, 459), Connection(459, 461), Connection(461, 458),
    Connection(364, 434), Connection(434, 394), Connection(394, 364),
    Connection(428, 396), Connection(396, 262), Connection(262, 428),
    Connection(274, 354), Connection(354, 457), Connection(457, 274),
    Connection(317, 316), Connection(316, 402), Connection(402, 317),
    Connection(316, 315), Connection(315, 403), Connection(403, 316),
    Connection(315, 314), Connection(314, 404), Connection(404, 315),
    Connection(314, 313), Connection(313, 405), Connection(405, 314),
    Connection(313, 421), Connection(421, 406), Connection(406, 313),
    Connection(323, 366), Connection(366, 361), Connection(361, 323),
    Connection(292, 306), Connection(306, 407), Connection(407, 292),
    Connection(306, 291), Connection(291, 408), Connection(408, 306),
    Connection(291, 287), Connection(287, 409), Connection(409, 291),
    Connection(287, 432), Connection(432, 410), Connection(410, 287),
    Connection(427, 434), Connection(434, 411), Connection(411, 427),
    Connection(372, 264), Connection(264, 383), Connection(383, 372),
    Connection(459, 309), Connection(309, 457), Connection(457, 459),
    Connection(366, 352), Connection(352, 401), Connection(401, 366),
    Connection(1, 274),   Connection(274, 4),   Connection(4, 1),
    Connection(418, 421), Connection(421, 262), Connection(262, 418),
    Connection(331, 294), Connection(294, 358), Connection(358, 331),
    Connection(435, 433), Connection(433, 367), Connection(367, 435),
    Connection(392, 289), Connection(289, 439), Connection(439, 392),
    Connection(328, 462), Connection(462, 326), Connection(326, 328),
    Connection(94, 2),    Connection(2, 370),   Connection(370, 94),
    Connection(289, 305), Connection(305, 455), Connection(455, 289),
    Connection(339, 254), Connection(254, 448), Connection(448, 339),
    Connection(359, 255), Connection(255, 446), Connection(446, 359),
    Connection(254, 253), Connection(253, 449), Connection(449, 254),
    Connection(253, 252), Connection(252, 450), Connection(450, 253),
    Connection(252, 256), Connection(256, 451), Connection(451, 252),
    Connection(256, 341), Connection(341, 452), Connection(452, 256),
    Connection(414, 413), Connection(413, 463), Connection(463, 414),
    Connection(286, 441), Connection(441, 414), Connection(414, 286),
    Connection(286, 258), Connection(258, 441), Connection(441, 286),
    Connection(258, 257), Connection(257, 442), Connection(442, 258),
    Connection(257, 259), Connection(259, 443), Connection(443, 257),
    Connection(259, 260), Connection(260, 444), Connection(444, 259),
    Connection(260, 467), Connection(467, 445), Connection(445, 260),
    Connection(309, 459), Connection(459, 250), Connection(250, 309),
    Connection(305, 289), Connection(289, 290), Connection(290, 305),
    Connection(305, 290), Connection(290, 460), Connection(460, 305),
    Connection(401, 376), Connection(376, 435), Connection(435, 401),
    Connection(309, 250), Connection(250, 392), Connection(392, 309),
    Connection(376, 411), Connection(411, 433), Connection(433, 376),
    Connection(453, 341), Connection(341, 464), Connection(464, 453),
    Connection(357, 453), Connection(453, 465), Connection(465, 357),
    Connection(343, 357), Connection(357, 412), Connection(412, 343),
    Connection(437, 343), Connection(343, 399), Connection(399, 437),
    Connection(344, 360), Connection(360, 440), Connection(440, 344),
    Connection(420, 437), Connection(437, 456), Connection(456, 420),
    Connection(360, 420), Connection(420, 363), Connection(363, 360),
    Connection(361, 401), Connection(401, 288), Connection(288, 361),
    Connection(265, 372), Connection(372, 353), Connection(353, 265),
    Connection(390, 339), Connection(339, 249), Connection(249, 390),
    Connection(339, 448), Connection(448, 255), Connection(255, 339)


@dataclasses.dataclass
class FaceLandmarkerResult:
  """The face landmarks detection result from FaceLandmarker, where each vector element represents a single face detected in the image.

  Attributes:
    face_landmarks: Detected face landmarks in normalized image coordinates.
    face_blendshapes: Optional face blendshapes results.
    facial_transformation_matrixes: Optional facial transformation matrix.
  """

  face_landmarks: List[List[landmark_module.NormalizedLandmark]]
  face_blendshapes: List[List[category_module.Category]]
  facial_transformation_matrixes: List[np.ndarray]


def _build_landmarker_result(
    output_packets: Mapping[str, packet_module.Packet]
) -> FaceLandmarkerResult:
  """Constructs a `FaceLandmarkerResult` from output packets."""
  face_landmarks_proto_list = packet_getter.get_proto_list(
      output_packets[_NORM_LANDMARKS_STREAM_NAME]
  )

  face_landmarks_results = []
  for proto in face_landmarks_proto_list:
    face_landmarks = landmark_pb2.NormalizedLandmarkList()
    face_landmarks.MergeFrom(proto)
    face_landmarks_list = []
    for face_landmark in face_landmarks.landmark:
      face_landmarks_list.append(
          landmark_module.NormalizedLandmark.create_from_pb2(face_landmark)
      )
    face_landmarks_results.append(face_landmarks_list)

  face_blendshapes_results = []
  if _BLENDSHAPES_STREAM_NAME in output_packets:
    face_blendshapes_proto_list = packet_getter.get_proto_list(
        output_packets[_BLENDSHAPES_STREAM_NAME]
    )
    for proto in face_blendshapes_proto_list:
      face_blendshapes_categories = []
      face_blendshapes_classifications = classification_pb2.ClassificationList()
      face_blendshapes_classifications.MergeFrom(proto)
      for face_blendshapes in face_blendshapes_classifications.classification:
        face_blendshapes_categories.append(
            category_module.Category(
                index=face_blendshapes.index,
                score=face_blendshapes.score,
                display_name=face_blendshapes.display_name,
                category_name=face_blendshapes.label,
            )
        )
      face_blendshapes_results.append(face_blendshapes_categories)

  facial_transformation_matrixes_results = []
  if _FACE_GEOMETRY_STREAM_NAME in output_packets:
    facial_transformation_matrixes_proto_list = packet_getter.get_proto_list(
        output_packets[_FACE_GEOMETRY_STREAM_NAME]
    )
    for proto in facial_transformation_matrixes_proto_list:
      if hasattr(proto, 'pose_transform_matrix'):
        matrix_data = matrix_data_pb2.MatrixData()
        matrix_data.MergeFrom(proto.pose_transform_matrix)
        matrix = np.array(matrix_data.packed_data)
        matrix = matrix.reshape((matrix_data.rows, matrix_data.cols))
        matrix = (
            matrix if matrix_data.layout == _LayoutEnum.ROW_MAJOR else matrix.T
        )
        facial_transformation_matrixes_results.append(matrix)

  return FaceLandmarkerResult(
      face_landmarks_results,
      face_blendshapes_results,
      facial_transformation_matrixes_results,
  )


@dataclasses.dataclass
class FaceLandmarkerOptions:
  """Options for the face landmarker task.

  Attributes:
    base_options: Base options for the face landmarker task.
    running_mode: The running mode of the task. Default to the image mode.
      HandLandmarker has three running modes: 1) The image mode for detecting
      face landmarks on single image inputs. 2) The video mode for detecting
      face landmarks on the decoded frames of a video. 3) The live stream mode
      for detecting face landmarks on the live stream of input data, such as
      from camera. In this mode, the "result_callback" below must be specified
      to receive the detection results asynchronously.
    num_faces: The maximum number of faces that can be detected by the
      FaceLandmarker.
    min_face_detection_confidence: The minimum confidence score for the face
      detection to be considered successful.
    min_face_presence_confidence: The minimum confidence score of face presence
      score in the face landmark detection.
    min_tracking_confidence: The minimum confidence score for the face tracking
      to be considered successful.
    output_face_blendshapes: Whether FaceLandmarker outputs face blendshapes
      classification. Face blendshapes are used for rendering the 3D face model.
    output_facial_transformation_matrixes: Whether FaceLandmarker outputs facial
      transformation_matrix. Facial transformation matrix is used to transform
      the face landmarks in canonical face to the detected face, so that users
      can apply face effects on the detected landmarks.
    result_callback: The user-defined result callback for processing live stream
      data. The result callback should only be specified when the running mode
      is set to the live stream mode.
  """

  base_options: _BaseOptions
  running_mode: _RunningMode = _RunningMode.IMAGE
  num_faces: Optional[int] = 1
  min_face_detection_confidence: Optional[float] = 0.5
  min_face_presence_confidence: Optional[float] = 0.5
  min_tracking_confidence: Optional[float] = 0.5
  output_face_blendshapes: Optional[bool] = False
  output_facial_transformation_matrixes: Optional[bool] = False
  result_callback: Optional[
      Callable[[FaceLandmarkerResult, image_module.Image, int], None]
  ] = None

  @doc_controls.do_not_generate_docs
  def to_pb2(self) -> _FaceLandmarkerGraphOptionsProto:
    """Generates an FaceLandmarkerGraphOptions protobuf object."""
    base_options_proto = self.base_options.to_pb2()
    base_options_proto.use_stream_mode = (
        False if self.running_mode == _RunningMode.IMAGE else True
    )

    # Initialize the face landmarker options from base options.
    face_landmarker_options_proto = _FaceLandmarkerGraphOptionsProto(
        base_options=base_options_proto
    )

    # Configure face detector options.
    face_landmarker_options_proto.face_detector_graph_options.num_faces = (
        self.num_faces
    )
    face_landmarker_options_proto.face_detector_graph_options.min_detection_confidence = (
        self.min_face_detection_confidence
    )

    # Configure face landmark detector options.
    face_landmarker_options_proto.min_tracking_confidence = (
        self.min_tracking_confidence
    )
    face_landmarker_options_proto.face_landmarks_detector_graph_options.min_detection_confidence = (
        self.min_face_detection_confidence
    )
    return face_landmarker_options_proto


class FaceLandmarker(base_vision_task_api.BaseVisionTaskApi):
  """Class that performs face landmarks detection on images."""

  @classmethod
  def create_from_model_path(cls, model_path: str) -> 'FaceLandmarker':
    """Creates an `FaceLandmarker` object from a TensorFlow Lite model and the default `FaceLandmarkerOptions`.

    Note that the created `FaceLandmarker` instance is in image mode, for
    detecting face landmarks on single image inputs.

    Args:
      model_path: Path to the model.

    Returns:
      `FaceLandmarker` object that's created from the model file and the
      default `FaceLandmarkerOptions`.

    Raises:
      ValueError: If failed to create `FaceLandmarker` object from the
        provided file such as invalid file path.
      RuntimeError: If other types of error occurred.
    """
    base_options = _BaseOptions(model_asset_path=model_path)
    options = FaceLandmarkerOptions(
        base_options=base_options, running_mode=_RunningMode.IMAGE
    )
    return cls.create_from_options(options)

  @classmethod
  def create_from_options(
      cls, options: FaceLandmarkerOptions
  ) -> 'FaceLandmarker':
    """Creates the `FaceLandmarker` object from face landmarker options.

    Args:
      options: Options for the face landmarker task.

    Returns:
      `FaceLandmarker` object that's created from `options`.

    Raises:
      ValueError: If failed to create `FaceLandmarker` object from
        `FaceLandmarkerOptions` such as missing the model.
      RuntimeError: If other types of error occurred.
    """

    def packets_callback(output_packets: Mapping[str, packet_module.Packet]):
      if output_packets[_IMAGE_OUT_STREAM_NAME].is_empty():
        return

      image = packet_getter.get_image(output_packets[_IMAGE_OUT_STREAM_NAME])
      if output_packets[_IMAGE_OUT_STREAM_NAME].is_empty():
        return

      if output_packets[_NORM_LANDMARKS_STREAM_NAME].is_empty():
        empty_packet = output_packets[_NORM_LANDMARKS_STREAM_NAME]
        options.result_callback(
            FaceLandmarkerResult([], [], []),
            image,
            empty_packet.timestamp.value // _MICRO_SECONDS_PER_MILLISECOND,
        )
        return

      face_landmarks_result = _build_landmarker_result(output_packets)
      timestamp = output_packets[_NORM_LANDMARKS_STREAM_NAME].timestamp
      options.result_callback(
          face_landmarks_result,
          image,
          timestamp.value // _MICRO_SECONDS_PER_MILLISECOND,
      )

    output_streams = [
        ':'.join([_NORM_LANDMARKS_TAG, _NORM_LANDMARKS_STREAM_NAME]),
        ':'.join([_IMAGE_TAG, _IMAGE_OUT_STREAM_NAME]),
    ]

    if options.output_face_blendshapes:
      output_streams.append(
          ':'.join([_BLENDSHAPES_TAG, _BLENDSHAPES_STREAM_NAME])
      )
    if options.output_facial_transformation_matrixes:
      output_streams.append(
          ':'.join([_FACE_GEOMETRY_TAG, _FACE_GEOMETRY_STREAM_NAME])
      )

    task_info = _TaskInfo(
        task_graph=_TASK_GRAPH_NAME,
        input_streams=[
            ':'.join([_IMAGE_TAG, _IMAGE_IN_STREAM_NAME]),
            ':'.join([_NORM_RECT_TAG, _NORM_RECT_STREAM_NAME]),
        ],
        output_streams=output_streams,
        task_options=options,
    )
    return cls(
        task_info.generate_graph_config(
            enable_flow_limiting=options.running_mode
            == _RunningMode.LIVE_STREAM
        ),
        options.running_mode,
        packets_callback if options.result_callback else None,
    )

  def detect(
      self,
      image: image_module.Image,
      image_processing_options: Optional[_ImageProcessingOptions] = None,
  ) -> FaceLandmarkerResult:
    """Performs face landmarks detection on the given image.

    Only use this method when the FaceLandmarker is created with the image
    running mode.

    The image can be of any size with format RGB or RGBA.
    TODO: Describes how the input image will be preprocessed after the yuv
    support is implemented.

    Args:
      image: MediaPipe Image.
      image_processing_options: Options for image processing.

    Returns:
      The face landmarks detection results.

    Raises:
      ValueError: If any of the input arguments is invalid.
      RuntimeError: If face landmarker detection failed to run.
    """
    normalized_rect = self.convert_to_normalized_rect(
        image_processing_options, image, roi_allowed=False
    )
    output_packets = self._process_image_data({
        _IMAGE_IN_STREAM_NAME: packet_creator.create_image(image),
        _NORM_RECT_STREAM_NAME: packet_creator.create_proto(
            normalized_rect.to_pb2()
        ),
    })

    if output_packets[_NORM_LANDMARKS_STREAM_NAME].is_empty():
      return FaceLandmarkerResult([], [], [])

    return _build_landmarker_result(output_packets)

  def detect_for_video(
      self,
      image: image_module.Image,
      timestamp_ms: int,
      image_processing_options: Optional[_ImageProcessingOptions] = None,
  ) -> FaceLandmarkerResult:
    """Performs face landmarks detection on the provided video frame.

    Only use this method when the FaceLandmarker is created with the video
    running mode.

    Only use this method when the FaceLandmarker is created with the video
    running mode. It's required to provide the video frame's timestamp (in
    milliseconds) along with the video frame. The input timestamps should be
    monotonically increasing for adjacent calls of this method.

    Args:
      image: MediaPipe Image.
      timestamp_ms: The timestamp of the input video frame in milliseconds.
      image_processing_options: Options for image processing.

    Returns:
      The face landmarks detection results.

    Raises:
      ValueError: If any of the input arguments is invalid.
      RuntimeError: If face landmarker detection failed to run.
    """
    normalized_rect = self.convert_to_normalized_rect(
        image_processing_options, image, roi_allowed=False
    )
    output_packets = self._process_video_data({
        _IMAGE_IN_STREAM_NAME: packet_creator.create_image(image).at(
            timestamp_ms * _MICRO_SECONDS_PER_MILLISECOND
        ),
        _NORM_RECT_STREAM_NAME: packet_creator.create_proto(
            normalized_rect.to_pb2()
        ).at(timestamp_ms * _MICRO_SECONDS_PER_MILLISECOND),
    })

    if output_packets[_NORM_LANDMARKS_STREAM_NAME].is_empty():
      return FaceLandmarkerResult([], [], [])

    return _build_landmarker_result(output_packets)

  def detect_async(
      self,
      image: image_module.Image,
      timestamp_ms: int,
      image_processing_options: Optional[_ImageProcessingOptions] = None,
  ) -> None:
    """Sends live image data to perform face landmarks detection.

    The results will be available via the "result_callback" provided in the
    FaceLandmarkerOptions. Only use this method when the FaceLandmarker is
    created with the live stream running mode.

    Only use this method when the FaceLandmarker is created with the live
    stream running mode. The input timestamps should be monotonically increasing
    for adjacent calls of this method. This method will return immediately after
    the input image is accepted. The results will be available via the
    `result_callback` provided in the `FaceLandmarkerOptions`. The
    `detect_async` method is designed to process live stream data such as
    camera input. To lower the overall latency, face landmarker may drop the
    input images if needed. In other words, it's not guaranteed to have output
    per input image.

    The `result_callback` provides:
      - The face landmarks detection results.
      - The input image that the face landmarker runs on.
      - The input timestamp in milliseconds.

    Args:
      image: MediaPipe Image.
      timestamp_ms: The timestamp of the input image in milliseconds.
      image_processing_options: Options for image processing.

    Raises:
      ValueError: If the current input timestamp is smaller than what the
      face landmarker has already processed.
    """
    normalized_rect = self.convert_to_normalized_rect(
        image_processing_options, image, roi_allowed=False
    )
    self._send_live_stream_data({
        _IMAGE_IN_STREAM_NAME: packet_creator.create_image(image).at(
            timestamp_ms * _MICRO_SECONDS_PER_MILLISECOND
        ),
        _NORM_RECT_STREAM_NAME: packet_creator.create_proto(
            normalized_rect.to_pb2()
        ).at(timestamp_ms * _MICRO_SECONDS_PER_MILLISECOND),
    })
