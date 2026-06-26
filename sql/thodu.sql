
SELECT COUNT(*)
FROM surat_housing;






DROP TABLE surti;


SELECT COUNT(*)
FROM surti;

DESCRIBE surat_housing;
SELECT *
FROM surat_housing
limit 5;

create table surti like surat_housing;
insert surti select * from surat_housing;

SELECT count(*)
FROM surti_clean;

ALTER TABLE surti
ADD COLUMN row_id INT AUTO_INCREMENT PRIMARY KEY;

create table surti_clean as
with duplicate_cte as(
	select *,
			ROW_NUMBER() over(
            partition by property_name,
						 areaWithType,
                         square_feet,
                         transaction,
                         status,
                         floor,
                         furnishing,
                         facing,
                         description,
                         price_per_sqft,
                         price
			order by row_id
		)as row_num
        
	from surti
)
SELECT *
FROM duplicate_cte
WHERE row_num = 1;



SELECT *
FROM surti_clean;

select distinct facing from surti_clean order by 1;

SELECT count(distinct facing)
FROM surti_clean;
-- 176 distinct values, way too many disticnt values for a direction(north,south,east,west,etc)
-- and almost 3000+ total values


select count(facing) from surti_clean;


select facing,count(*) as freq
from surti_clean
where facing is not null
group by facing
order by freq desc;
-- E:1463
-- SW:351
-- NE:233
-- N:97
-- W:90
-- SE: 55
-- S:35
-- NW:25
-- above are the only valid directions provided in the dataset, most probably webscraped the data in a messy way
-- Rest all values are probably missed place(e.g: amentites and society names)




UPDATE surti_clean
SET facing = TRIM(facing);







SELECT COUNT(*)
FROM surti_clean
WHERE facing NOT IN (
    'East',
    'West',
    'North',
    'South',
    'North - East',
    'North - West',
    'South - East',
    'South -West'
)
AND facing IS NOT NULL;

-- 1504 values which are wrong, 2349 values are actually correct and represent the facing direction,
-- 3853 total values in facing

UPDATE surti_clean
SET facing = 'North-East'
WHERE facing = 'North - East';

UPDATE surti_clean
SET facing = 'North-West'
WHERE facing = 'North - West';

UPDATE surti_clean
SET facing = 'South-East'
WHERE facing = 'South - East';

UPDATE surti_clean
SET facing = 'South-West'
WHERE facing = 'South -West';

-- standardized names of the directions.

SELECT COUNT(*)
FROM surti_clean
WHERE facing NOT IN (
    'East',
    'West',
    'North',
    'South',
    'North-East',
    'North-West',
    'South-East',
    'South-West'
)
AND facing IS NOT NULL;

-- we use this to confirm whther there are 1504 wrong values, which would be nulled



UPDATE surti_clean
SET facing = NULL
WHERE facing NOT IN (
    'East',
    'West',
    'North',
    'South',
    'North-East',
    'North-West',
    'South-East',
    'South-West'
)
AND facing IS NOT NULL;
-- now we have converted the wrong facings into NULL

select * from surti_clean;








select * from surti_clean;

select count(areaWithType)
from surti_clean
where areaWithType like '%Area%'
and areaWithType is not null;

-- 4410 values which have correct Area type

select count(areaWithType)
from surti_clean
where areaWithType not in( 'Super Area','Built Area','Carpet Area','Plot Area')
and areaWithType is not null;

-- 6 wrong values,

select distinct areaWithType
from surti_clean;
-- transaction and status are wrong values here, they arent Area types


update surti_clean
set areaWithType = null
where areaWithType not in( 'Super Area','Built Area','Carpet Area','Plot Area')
and areaWithType is not null;









-- square_feet

select count(square_feet)
from surti_clean
where square_feet not like '%sqft%' and square_feet not like '%sqyrd%' and square_feet not like '%sqm%' and square_feet not like '%acre%'
and square_feet is not null;

-- 4416 :total values->(breakdown below)
-- 8 values which dont have the units sqft and sqyrds
-- 4228 values with sqft
-- 154 values with sqyrd
-- 25 values with sqm
-- 1 value with acre



SELECT  distinct square_feet
FROM surti_clean
WHERE square_feet NOT LIKE '%sqft%'
  AND square_feet NOT LIKE '%sqyrd%'
  AND square_feet NOT LIKE '%sqm%'
  AND square_feet NOT LIKE '%acre%'
  AND square_feet IS NOT NULL;
  
-- a good practice to check all the possible correct units ,so they dont get mistankely nulled ahead, for e.g i forgot about sqm and acre(only a singular value)

update surti_clean
set square_feet = null
where square_feet not like '%sqft%' and square_feet not like '%sqyrd%' and square_feet not like '%sqm%' and square_feet not like '%acre%'
and square_feet is not null;

-- wrong values replaced with NULL

SELECT square_feet, COUNT(*) AS freq
FROM surti_clean
WHERE square_feet IS NOT NULL
GROUP BY square_feet
ORDER BY freq DESC
limit 20;
-- final checking to find errors in naming

select * from surti_clean;



ALTER TABLE surti_clean
ADD COLUMN sqft_numeric DECIMAL(12,2);
-- now i created a new column , which has all the values in sqft


UPDATE surti_clean
SET sqft_numeric =
    CAST(REPLACE(square_feet, ' sqft', '') AS DECIMAL(12,2))
WHERE square_feet LIKE '%sqft%';


UPDATE surti_clean
SET sqft_numeric =
    CAST(REPLACE(square_feet, ' sqyrd', '') AS DECIMAL(12,2)) * 9
WHERE square_feet LIKE '%sqyrd%';



UPDATE surti_clean
SET sqft_numeric =
    CAST(REPLACE(square_feet, ' acre', '') AS DECIMAL(12,2)) * 43560
WHERE square_feet LIKE '%acre%';

UPDATE surti_clean
SET sqft_numeric =
    CAST(
        REPLACE(
            REPLACE(square_feet,' sqm',''),
            ',',''
        ) AS DECIMAL(12,2)
    ) * 10.7639
WHERE square_feet LIKE '%sqm%';

-- took care of commas from sqm






-- price
-- select distinct price from surti_clean group by price  having price like '%Cr%' order by price;
select price,sale_price from surti_clean;
select count(price) from surti_clean where price like '%Lac%';
select count(price) from surti_clean where price like '%Cr%';
select count(price) from surti_clean where price like '%Call%';
select count(price) from surti_clean where price is NULL;
select 2757+1487+172 as total;
-- No. of values:
-- Lac: 2757
-- Cr: 1487 
-- Call for Price: 172
-- Zero NUll values :)
-- Total values in price column:4416 

alter table surti_clean
add column sale_price bigint;
-- using bigint to hold large decimals, like 1 or 20 Cr.

SELECT DISTINCT price
FROM surti_clean
LIMIT 100;
-- safe practice to check for mistakes manually,

UPDATE surti_clean
SET sale_price =
    CAST(
        REPLACE(
            REPLACE(price,'₹',''),
            ' Lac',''
        ) AS DECIMAL(10,2)
    ) * 100000
WHERE price LIKE '%Lac%';


update surti_clean
set sale_price = cast(replace(replace(price,'₹',''),' Cr','') as decimal(12,2))*10000000 where price like '%Cr%';

-- inserted the values of lac and cr , but only the int value

SELECT COUNT(price),
       COUNT(sale_price)
FROM surti_clean;

SELECT COUNT(*) from surti_clean where sale_price is null;

-- count of price = 4416
-- count of sale_price = 4244
-- Call for price are null (172)








-- transaction
select distinct transaction from surti_clean;
select * from surti_clean;

SELECT COUNT(*)
FROM surti_clean
WHERE transaction NOT IN ('New Property','Resale')
AND transaction IS NOT NULL;

SELECT COUNT(*)
FROM surti_clean
WHERE transaction IS NULL;

select transaction, count(*) as freq from surti_clean group by transaction order by freq desc;

-- 713 vwrong values(not null)
-- 103 null values already
-- Resale: 2129
-- New Property: 1471

select transaction,furnishing from surti_clean where furnishing is null and transaction like '%semi-furnished%';

UPDATE surti_clean
SET transaction = NULL
WHERE transaction NOT IN (
    'New Property',
    'Resale'
);
-- 816 null values now
-- Resale: 2129
-- New Property: 1471




-- furnishing

select * from surti_clean;

select distinct furnishing from surti_clean;

SELECT furnishing, COUNT(*)
FROM surti_clean
GROUP BY furnishing
ORDER BY COUNT(*) DESC;


SELECT COUNT(*)
FROM surti_clean
WHERE furnishing NOT IN (
    'Unfurnished',
    'Semi-Furnished',
    'Furnished'
)
AND furnishing IS NOT NULL;

UPDATE surti_clean
SET furnishing = NULL
WHERE furnishing NOT IN (
    'Unfurnished',
    'Semi-Furnished',
    'Furnished'
)
AND furnishing IS NOT NULL;

-- 'Unfurnished','2286'
-- NULL,'1212'
-- 'Semi-Furnished','475'
-- 'Furnished','443'

select 2286+1212+475+443 
-- total is still 4416, yay


-- status --
select count(status) from surti_clean;

select status,count(*) from surti_clean group by status order by count(*) desc;


select status, count(*)
from surti_clean 
where(status like'%Poss. by%' or status like 'Ready to Move') 
and status is not null
group by status  order by count(*) desc;



update surti_clean
set status = null
WHERE (status NOT LIKE '%Poss. by%'
  AND status <> 'Ready to Move'
  AND status IS NOT NULL);
  
-- 4095 valid values
-- 321 null values
  


select count(floor) from surti_clean;

select floor,count(*) from surti_clean group by floor order by count(*) desc;

select floor,count(*) 
from surti_clean
where floor like '%out of%'
and floor is not null
group by floor
order by count(*) desc;


select floor,count(*) 
from surti_clean
where floor not like '%out of%'
and floor is not null
group by floor
order by count(*) desc;

-- 809 is null 

SELECT DISTINCT floor
FROM surti_clean
WHERE floor NOT LIKE '%out of%'
  AND floor IS NOT NULL;
  
  
  
UPDATE surti_clean
SET floor = NULL
WHERE floor IN (
    'Yes',
    'No',
    'Resale',
    'Unfurnished',
    'Om Residency'
);

  
UPDATE surti_clean
SET floor = NULL
WHERE( floor NOT LIKE '%out of%' and floor <> 'Ground'
  AND floor IS NOT NULL);

SELECT floor, COUNT(*)
FROM surti_clean
WHERE floor IN ('1','2','3','4','5')
GROUP BY floor;

select 854+3562;
-- 854 null values
-- 3562 other values

select *from surti_clean;



-- price_per_sqft

ALTER TABLE surti_clean
ADD COLUMN price_per_sqft_numeric INT;

update surti_clean
set price_per_sqft_numeric = cast(replace(replace(price_per_sqft,'₹',''),' per sqft','')as unsigned)
WHERE price_per_sqft IS NOT NULL;


update surti_clean 
set price_per_sqft_numeric =
cast(replace(replace(replace(price_per_sqft,'₹',''),',',''),' per sqft','')as unsigned)
WHERE price_per_sqft IS NOT NULL;



select price_per_sqft,price_per_sqft_numeric from surti_clean;




SELECT
COUNT(*) total_rows, 
COUNT(property_name) property_name,
COUNT(areaWithType) areaWithType,
COUNT(square_feet) square_feet,
COUNT(transaction) transaction,
COUNT(status) status,
COUNT(floor) floor,
COUNT(furnishing) furnishing,
COUNT(facing) facing,
COUNT(description) description,
COUNT(price_per_sqft) price_per_sqft,
COUNT(price) price
FROM surti_clean;

select * from surti_clean;


