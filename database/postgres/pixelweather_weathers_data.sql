--
-- PostgreSQL database dump
--

\restrict feNUV6IhuNsMGqIcHBwhPsp2256ZXGupu4zG9WLUgJshFKF14GoPJYF18ykaJz7

-- Dumped from database version 17.5 (Debian 17.5-1.pgdg120+1)
-- Dumped by pg_dump version 17.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: weathers; Type: TABLE DATA; Schema: pixelweather; Owner: -
--

COPY pixelweather.weathers (id, category_id, weather, weather_code) FROM stdin;
1	1	thunderstorm with light rain	200
2	1	thunderstorm with rain	201
3	1	thunderstorm with heavy rain	202
4	1	light thunderstorm	210
5	1	thunderstorm	211
6	1	heavy thunderstorm	212
7	1	ragged thunderstorm	221
8	1	thunderstorm with light drizzle	230
9	1	thunderstorm with drizzle	231
10	1	thunderstorm with heavy drizzle	232
11	2	light intensity drizzle	300
12	2	drizzle	301
13	2	heavy intensity drizzle	302
14	2	light intensity drizzle rain	310
15	2	drizzle rain	311
16	2	heavy intensity drizzle rain	312
17	2	shower rain and drizzle	313
18	2	heavy shower rain and drizzle	314
19	2	shower drizzle	321
20	3	light rain	500
21	3	moderate rain	501
22	3	heavy intensity rain	502
23	3	very heavy rain	503
24	3	extreme rain	504
25	3	freezing rain	511
26	3	light intensity shower rain	520
27	3	shower rain	521
28	3	heavy intensity shower rain	522
29	3	ragged shower rain	531
30	4	mist	701
31	4	smoke	711
32	4	haze	721
33	4	sand/dust whirls	731
34	4	fog	741
35	4	sand	751
36	4	dust	761
37	4	volcanic ash	762
38	4	squalls	771
39	4	tornado	781
40	5	clear sky	800
41	6	few clouds: 11-25%	801
42	6	scattered clouds: 25-50%	802
43	6	broken clouds: 51-84%	803
44	6	overcast clouds: 85-100%	804
45	7	windy	900
46	8	storm	901
47	9	hail	902
48	10	hot	903
49	10	cold	904
\.


--
-- Name: weathers_id_seq; Type: SEQUENCE SET; Schema: pixelweather; Owner: -
--

SELECT pg_catalog.setval('pixelweather.weathers_id_seq', 49, true);


--
-- PostgreSQL database dump complete
--

\unrestrict feNUV6IhuNsMGqIcHBwhPsp2256ZXGupu4zG9WLUgJshFKF14GoPJYF18ykaJz7

