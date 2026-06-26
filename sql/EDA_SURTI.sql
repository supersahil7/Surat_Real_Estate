select property_name from surti_clean ;
select count(*) from surti_clean;

select distinct areaWithType  from surti_clean;
-- =================================================

SELECT
    MIN(sale_price),
    MAX(sale_price),
    ROUND(AVG(sale_price),0)
FROM surti_clean;

SELECT square_feet,price,price_per_sqft
FROM surti_clean
WHERE sqft_numeric > 10000;

SELECT property_name,
       sale_price,
       price,
       square_feet
FROM surti_clean
ORDER BY sale_price DESC
LIMIT 20;



-- =========================================
-- EDA.1.Impact of facing on Price
SELECT facing,
       COUNT(*) AS listings,
       ROUND(AVG(sale_price),0) AS avg_price,
       ROUND(AVG(price_per_sqft_numeric),0) AS avg_price_per_sqft
FROM surti_clean
WHERE facing IS NOT NULL
GROUP BY facing
ORDER BY avg_price DESC;



WITH ranked AS (
    SELECT facing,
           sale_price,
           ROW_NUMBER() OVER (
               PARTITION BY facing
               ORDER BY sale_price
           ) AS rn,
           COUNT(*) OVER (
               PARTITION BY facing
           ) AS cnt
    FROM surti_clean
    WHERE facing IS NOT NULL
)
SELECT facing,
       ROUND(AVG(sale_price),0) AS median_price
FROM ranked
WHERE rn IN (
    FLOOR((cnt + 1)/2),
    FLOOR((cnt + 2)/2)
)
GROUP BY facing;

-- =========================================
-- EDA.2.Impact of area type on price:
-- =========================================


SELECT areaWithType,
       ROUND(AVG(price_per_sqft_numeric),0) avg_pps,
       COUNT(*) listings
FROM surti_clean
GROUP BY areaWithType;


SELECT property_name,
       price_per_sqft_numeric,
       areaWithType
FROM surti_clean
WHERE areaWithType = 'Built Area'
ORDER BY price_per_sqft_numeric DESC
LIMIT 20;

WITH ranked AS (
    SELECT areaWithType,
           price_per_sqft_numeric,
           ROW_NUMBER() OVER (
               PARTITION BY areaWithType
               ORDER BY price_per_sqft_numeric
           ) AS rn,
           COUNT(*) OVER (
               PARTITION BY areaWithType
           ) AS cnt
    FROM surti_clean
    WHERE areaWithType IS NOT NULL
      AND price_per_sqft_numeric IS NOT NULL
)
SELECT areaWithType,
       ROUND(AVG(price_per_sqft_numeric),0) AS median_price_per_sqft
FROM ranked
WHERE rn IN (
    FLOOR((cnt + 1)/2),
    FLOOR((cnt + 2)/2)
)
GROUP BY areaWithType
ORDER BY median_price_per_sqft DESC;

-- ============================================
-- EDA.3. New property vs resale
-- ============================================
SELECT transaction,
       ROUND(AVG(price_per_sqft_numeric),0) avg_pps,
       COUNT(*) listings
FROM surti_clean
GROUP BY transaction;

WITH ranked AS (
    SELECT transaction,
           sale_price,
           ROW_NUMBER() OVER (
               PARTITION BY transaction
               ORDER BY sale_price
           ) AS rn,
           COUNT(*) OVER (
               PARTITION BY transaction
           ) AS cnt
    FROM surti_clean
    WHERE transaction IN ('Resale','New Property')
      AND sale_price IS NOT NULL
)
SELECT transaction,
       ROUND(AVG(sale_price),0) AS median_price
FROM ranked
WHERE rn IN (
    FLOOR((cnt + 1)/2),
    FLOOR((cnt + 2)/2)
)
GROUP BY transaction;

SELECT facing,
       SUM(CASE WHEN transaction = 'Resale' THEN 1 ELSE 0 END) AS resale_count,
       SUM(CASE WHEN transaction = 'New Property' THEN 1 ELSE 0 END) AS new_property_count
FROM surti_clean
WHERE transaction IN ('Resale','New Property')
  AND facing IS NOT NULL
GROUP BY facing
ORDER BY facing;


-- ============================================
-- EDA.4.Furnishing vs property price   
-- ============================================

SELECT furnishing,
       COUNT(*) listings,
       ROUND(AVG(sale_price),0) avg_price
FROM surti_clean
WHERE furnishing IS NOT NULL
GROUP BY furnishing;

WITH ranked AS (
    SELECT furnishing,
           sale_price,
           ROW_NUMBER() OVER (
               PARTITION BY furnishing
               ORDER BY sale_price
           ) AS rn,
           COUNT(*) OVER (
               PARTITION BY furnishing
           ) AS cnt
    FROM surti_clean
    WHERE furnishing IN ('Furnished','Semi-Furnished','Unfurnished')
      AND sale_price IS NOT NULL
)
SELECT furnishing,
       ROUND(AVG(sale_price),0) AS median_price
FROM ranked
WHERE rn IN (
    FLOOR((cnt + 1)/2),
    FLOOR((cnt + 2)/2)
)
GROUP BY furnishing
ORDER BY median_price DESC;

-- ============================================
-- EDA.5.Floor vs Property Price  
-- ============================================

SELECT
    CASE
        WHEN floor LIKE 'Ground%' THEN 'Ground Floor'
        ELSE 'Upper Floors'
    END AS floor_type,
    COUNT(*) AS listings,
    ROUND(AVG(sale_price),0) AS avg_price
FROM surti_clean
WHERE floor IS NOT NULL
GROUP BY floor_type;

WITH ranked AS (
    SELECT
        CASE
            WHEN floor LIKE 'Ground%' THEN 'Ground Floor'
            ELSE 'Upper Floors'
        END AS floor_type,
        sale_price,
        ROW_NUMBER() OVER (
            PARTITION BY
                CASE
                    WHEN floor LIKE 'Ground%' THEN 'Ground Floor'
                    ELSE 'Upper Floors'
                END
            ORDER BY sale_price
        ) AS rn,
        COUNT(*) OVER (
            PARTITION BY
                CASE
                    WHEN floor LIKE 'Ground%' THEN 'Ground Floor'
                    ELSE 'Upper Floors'
                END
        ) AS cnt
    FROM surti_clean
    WHERE floor IS NOT NULL
      AND sale_price IS NOT NULL
)
SELECT floor_type,
       ROUND(AVG(sale_price),0) AS median_price
FROM ranked
WHERE rn IN (
    FLOOR((cnt + 1)/2),
    FLOOR((cnt + 2)/2)
)
GROUP BY floor_type;



-- --
SELECT
    CASE
        WHEN floor = 'Ground' THEN 'Ground Floor'
        WHEN CAST(SUBSTRING_INDEX(floor,' out of',1) AS UNSIGNED) BETWEEN 1 AND 3
            THEN 'Low Floor (1-3)'
        WHEN CAST(SUBSTRING_INDEX(floor,' out of',1) AS UNSIGNED) BETWEEN 4 AND 8
            THEN 'Mid Floor (4-8)'
        ELSE 'High Floor (9+)'
    END AS floor_category,
    COUNT(*) AS listings
FROM surti_clean
WHERE floor IS NOT NULL
GROUP BY floor_category;
--
SELECT
    CASE
        WHEN floor = 'Ground' THEN 'Ground Floor'
        WHEN CAST(SUBSTRING_INDEX(floor,' out of',1) AS UNSIGNED) BETWEEN 1 AND 3
            THEN 'Low Floor (1-3)'
        WHEN CAST(SUBSTRING_INDEX(floor,' out of',1) AS UNSIGNED) BETWEEN 4 AND 8
            THEN 'Mid Floor (4-8)'
        ELSE 'High Floor (9+)'
    END AS floor_category,
    COUNT(*) AS listings,
    ROUND(AVG(sale_price),0) AS avg_price
FROM surti_clean
WHERE floor IS NOT NULL
GROUP BY floor_category;

-- ======
WITH ranked AS (
    SELECT
        CASE
            WHEN floor = 'Ground' THEN 'Ground Floor'
            WHEN CAST(SUBSTRING_INDEX(floor,' out of',1) AS UNSIGNED) BETWEEN 1 AND 3
                THEN 'Low Floor (1-3)'
            WHEN CAST(SUBSTRING_INDEX(floor,' out of',1) AS UNSIGNED) BETWEEN 4 AND 8
                THEN 'Mid Floor (4-8)'
            ELSE 'High Floor (9+)'
        END AS floor_category,
        sale_price,
        ROW_NUMBER() OVER (
            PARTITION BY
                CASE
                    WHEN floor = 'Ground' THEN 'Ground Floor'
                    WHEN CAST(SUBSTRING_INDEX(floor,' out of',1) AS UNSIGNED) BETWEEN 1 AND 3
                        THEN 'Low Floor (1-3)'
                    WHEN CAST(SUBSTRING_INDEX(floor,' out of',1) AS UNSIGNED) BETWEEN 4 AND 8
                        THEN 'Mid Floor (4-8)'
                    ELSE 'High Floor (9+)'
                END
            ORDER BY sale_price
        ) AS rn,
        COUNT(*) OVER (
            PARTITION BY
                CASE
                    WHEN floor = 'Ground' THEN 'Ground Floor'
                    WHEN CAST(SUBSTRING_INDEX(floor,' out of',1) AS UNSIGNED) BETWEEN 1 AND 3
                        THEN 'Low Floor (1-3)'
                    WHEN CAST(SUBSTRING_INDEX(floor,' out of',1) AS UNSIGNED) BETWEEN 4 AND 8
                        THEN 'Mid Floor (4-8)'
                    ELSE 'High Floor (9+)'
                END
        ) AS cnt
    FROM surti_clean
    WHERE floor IS NOT NULL
)
SELECT floor_category,
       ROUND(AVG(sale_price),0) AS median_price
FROM ranked
WHERE rn IN (
    FLOOR((cnt + 1)/2),
    FLOOR((cnt + 2)/2)
)
GROUP BY floor_category;







-- ==================================================================================
-- EDA.6.Area vs Property Price  
-- ==================================================================================

SELECT
    CASE
        WHEN sqft_numeric < 1000 THEN 'Small (<1000 sqft)'
        WHEN sqft_numeric BETWEEN 1000 AND 2000 THEN 'Medium (1000-2000 sqft)'
        WHEN sqft_numeric BETWEEN 2001 AND 4000 THEN 'Large (2001-4000 sqft)'
        ELSE 'Luxury (4000+ sqft)'
    END AS area_category,
    COUNT(*) AS listings,
    ROUND(AVG(sale_price),0) AS avg_price
FROM surti_clean
WHERE sqft_numeric IS NOT NULL
GROUP BY area_category
ORDER BY avg_price;


--
WITH ranked AS (
    SELECT
        CASE
            WHEN sqft_numeric < 1000 THEN 'Small (<1000 sqft)'
            WHEN sqft_numeric BETWEEN 1000 AND 2000 THEN 'Medium (1000-2000 sqft)'
            WHEN sqft_numeric BETWEEN 2001 AND 4000 THEN 'Large (2001-4000 sqft)'
            ELSE 'Luxury (4000+ sqft)'
        END AS area_category,
        sale_price,
        ROW_NUMBER() OVER (
            PARTITION BY
                CASE
                    WHEN sqft_numeric < 1000 THEN 'Small (<1000 sqft)'
                    WHEN sqft_numeric BETWEEN 1000 AND 2000 THEN 'Medium (1000-2000 sqft)'
                    WHEN sqft_numeric BETWEEN 2001 AND 4000 THEN 'Large (2001-4000 sqft)'
                    ELSE 'Luxury (4000+ sqft)'
                END
            ORDER BY sale_price
        ) AS rn,
        COUNT(*) OVER (
            PARTITION BY
                CASE
                    WHEN sqft_numeric < 1000 THEN 'Small (<1000 sqft)'
                    WHEN sqft_numeric BETWEEN 1000 AND 2000 THEN 'Medium (1000-2000 sqft)'
                    WHEN sqft_numeric BETWEEN 2001 AND 4000 THEN 'Large (2001-4000 sqft)'
                    ELSE 'Luxury (4000+ sqft)'
                END
        ) AS cnt
    FROM surti_clean
    WHERE sqft_numeric IS NOT NULL
)
SELECT area_category,
       ROUND(AVG(sale_price),0) AS median_price
FROM ranked
WHERE rn IN (
    FLOOR((cnt + 1)/2),
    FLOOR((cnt + 2)/2)
)
GROUP BY area_category
ORDER BY median_price;



-- ==================================================================================
-- EDA.7.Luxury Market Segmentation Analysis  
-- ==================================================================================


SELECT
    CASE
        WHEN sale_price < 5000000 THEN 'Budget (<50L)'
        WHEN sale_price < 10000000 THEN 'Mid-Range (50L-1Cr)'
        WHEN sale_price < 20000000 THEN 'Premium (1Cr-2Cr)'
        ELSE 'Luxury (>2Cr)'
    END AS segment,
    COUNT(*) AS listings,
    ROUND(COUNT(*) * 100.0 /
        (SELECT COUNT(*) FROM surti_clean WHERE sale_price IS NOT NULL),2)
        AS percentage
FROM surti_clean
GROUP BY segment
ORDER BY MIN(sale_price);



-- ==================================================================================
-- EDA.8.Luxury Market Segmentation Analysis  
-- ==================================================================================
SELECT property_name,
       sale_price,
       sqft_numeric,
       price_per_sqft_numeric,
       description
FROM surti_clean
ORDER BY sale_price DESC
LIMIT 12;




-- ==================================================================================
-- EDA.9.Impact of Property Type on Pricing  
-- ==================================================================================
WITH ranked AS (
    SELECT
        CASE
            WHEN property_name LIKE '%1 BHK%' THEN '1 BHK'
            WHEN property_name LIKE '%2 BHK%' THEN '2 BHK'
            WHEN property_name LIKE '%3 BHK%' THEN '3 BHK'
            WHEN property_name LIKE '%4 BHK%' THEN '4 BHK'
            WHEN property_name LIKE '%5 BHK%' THEN '5+ BHK'
            WHEN property_name LIKE '%House%' THEN 'House'
            WHEN property_name LIKE '%Villa%' THEN 'Villa'
            WHEN property_name LIKE '%Office Space%' THEN 'Office Space'
            WHEN property_name LIKE '%Shop%' THEN 'Shop'
            WHEN property_name LIKE '%Showroom%' THEN 'Showroom'
            WHEN property_name LIKE '%Industrial%' THEN 'Industrial'
            WHEN property_name LIKE '%Plot/Land%'
              OR property_name LIKE '%Land for Sale%' THEN 'Land/Plot'
            ELSE 'Other'
        END AS property_type,
        sale_price,
        ROW_NUMBER() OVER (
            PARTITION BY
                CASE
                    WHEN property_name LIKE '%1 BHK%' THEN '1 BHK'
                    WHEN property_name LIKE '%2 BHK%' THEN '2 BHK'
                    WHEN property_name LIKE '%3 BHK%' THEN '3 BHK'
                    WHEN property_name LIKE '%4 BHK%' THEN '4 BHK'
                    WHEN property_name LIKE '%5 BHK%' THEN '5+ BHK'
                    WHEN property_name LIKE '%House%' THEN 'House'
                    WHEN property_name LIKE '%Villa%' THEN 'Villa'
                    WHEN property_name LIKE '%Office Space%' THEN 'Office Space'
                    WHEN property_name LIKE '%Shop%' THEN 'Shop'
                    WHEN property_name LIKE '%Showroom%' THEN 'Showroom'
                    WHEN property_name LIKE '%Industrial%' THEN 'Industrial'
                    WHEN property_name LIKE '%Plot/Land%'
                      OR property_name LIKE '%Land for Sale%' THEN 'Land/Plot'
                    ELSE 'Other'
                END
            ORDER BY sale_price
        ) rn,
        COUNT(*) OVER (
            PARTITION BY
                CASE
                    WHEN property_name LIKE '%1 BHK%' THEN '1 BHK'
                    WHEN property_name LIKE '%2 BHK%' THEN '2 BHK'
                    WHEN property_name LIKE '%3 BHK%' THEN '3 BHK'
                    WHEN property_name LIKE '%4 BHK%' THEN '4 BHK'
                    WHEN property_name LIKE '%5 BHK%' THEN '5+ BHK'
                    WHEN property_name LIKE '%House%' THEN 'House'
                    WHEN property_name LIKE '%Villa%' THEN 'Villa'
                    WHEN property_name LIKE '%Office Space%' THEN 'Office Space'
                    WHEN property_name LIKE '%Shop%' THEN 'Shop'
                    WHEN property_name LIKE '%Showroom%' THEN 'Showroom'
                    WHEN property_name LIKE '%Industrial%' THEN 'Industrial'
                    WHEN property_name LIKE '%Plot/Land%'
                      OR property_name LIKE '%Land for Sale%' THEN 'Land/Plot'
                    ELSE 'Other'
                END
        ) cnt
    FROM surti_clean
    WHERE sale_price IS NOT NULL
)
SELECT
    property_type,
    ROUND(AVG(sale_price),0) AS median_price
FROM ranked
WHERE rn IN (
    FLOOR((cnt + 1)/2),
    FLOOR((cnt + 2)/2)
)
GROUP BY property_type
ORDER BY median_price DESC;

-- ========

WITH ranked AS (
    SELECT
        CASE
            WHEN property_name LIKE '%1 BHK%' THEN '1 BHK'
            WHEN property_name LIKE '%2 BHK%' THEN '2 BHK'
            WHEN property_name LIKE '%3 BHK%' THEN '3 BHK'
            WHEN property_name LIKE '%4 BHK%' THEN '4 BHK'
            WHEN property_name LIKE '%5 BHK%' THEN '5+ BHK'
            WHEN property_name LIKE '%House%' THEN 'House'
            WHEN property_name LIKE '%Villa%' THEN 'Villa'
            WHEN property_name LIKE '%Office Space%' THEN 'Office Space'
            WHEN property_name LIKE '%Shop%' THEN 'Shop'
            WHEN property_name LIKE '%Showroom%' THEN 'Showroom'
            WHEN property_name LIKE '%Industrial%' THEN 'Industrial'
            WHEN property_name LIKE '%Plot/Land%'
              OR property_name LIKE '%Land for Sale%' THEN 'Land/Plot'
            ELSE 'Other'
        END AS property_type,
        price_per_sqft_numeric,
        ROW_NUMBER() OVER (
            PARTITION BY
                CASE
                    WHEN property_name LIKE '%1 BHK%' THEN '1 BHK'
                    WHEN property_name LIKE '%2 BHK%' THEN '2 BHK'
                    WHEN property_name LIKE '%3 BHK%' THEN '3 BHK'
                    WHEN property_name LIKE '%4 BHK%' THEN '4 BHK'
                    WHEN property_name LIKE '%5 BHK%' THEN '5+ BHK'
                    WHEN property_name LIKE '%House%' THEN 'House'
                    WHEN property_name LIKE '%Villa%' THEN 'Villa'
                    WHEN property_name LIKE '%Office Space%' THEN 'Office Space'
                    WHEN property_name LIKE '%Shop%' THEN 'Shop'
                    WHEN property_name LIKE '%Showroom%' THEN 'Showroom'
                    WHEN property_name LIKE '%Industrial%' THEN 'Industrial'
                    WHEN property_name LIKE '%Plot/Land%'
                      OR property_name LIKE '%Land for Sale%' THEN 'Land/Plot'
                    ELSE 'Other'
                END
            ORDER BY price_per_sqft_numeric
        ) rn,
        COUNT(*) OVER (
            PARTITION BY
                CASE
                    WHEN property_name LIKE '%1 BHK%' THEN '1 BHK'
                    WHEN property_name LIKE '%2 BHK%' THEN '2 BHK'
                    WHEN property_name LIKE '%3 BHK%' THEN '3 BHK'
                    WHEN property_name LIKE '%4 BHK%' THEN '4 BHK'
                    WHEN property_name LIKE '%5 BHK%' THEN '5+ BHK'
                    WHEN property_name LIKE '%House%' THEN 'House'
                    WHEN property_name LIKE '%Villa%' THEN 'Villa'
                    WHEN property_name LIKE '%Office Space%' THEN 'Office Space'
                    WHEN property_name LIKE '%Shop%' THEN 'Shop'
                    WHEN property_name LIKE '%Showroom%' THEN 'Showroom'
                    WHEN property_name LIKE '%Industrial%' THEN 'Industrial'
                    WHEN property_name LIKE '%Plot/Land%'
                      OR property_name LIKE '%Land for Sale%' THEN 'Land/Plot'
                    ELSE 'Other'
                END
        ) cnt
    FROM surti_clean
    WHERE price_per_sqft_numeric IS NOT NULL
)
SELECT
    property_type,
    ROUND(AVG(price_per_sqft_numeric),0) AS median_ppsqft
FROM ranked
WHERE rn IN (
    FLOOR((cnt + 1)/2),
    FLOOR((cnt + 2)/2)
)
GROUP BY property_type
ORDER BY median_ppsqft DESC;