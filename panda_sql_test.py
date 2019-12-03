"""
Test cases for panda to sql
"""
# pylint: disable=broad-except
import numpy as np
from pandas import read_csv, merge, concat
from sql_to_pandas import SqlToPandas
from sql_exception import MultipleQueriesException, InvalidQueryException, DataFrameDoesNotExist

FOREST_FIRES = read_csv('~/PycharmProjects/sql_to_pandas/data/forestfires.csv') # Name is weird intentionally

DIGIMON_MON_LIST = read_csv('~/PycharmProjects/sql_to_pandas/data/DigiDB_digimonlist.csv')
DIGIMON_MOVE_LIST = read_csv('~/PycharmProjects/sql_to_pandas/data/DigiDB_movelist.csv')
DIGIMON_SUPPORT_LIST = read_csv('~/PycharmProjects/sql_to_pandas/data/DigiDB_supportlist.csv')
DIGIMON_MON_LIST['mon_attribute'] = DIGIMON_MON_LIST['Attribute']
DIGIMON_MOVE_LIST['move_attribute'] = DIGIMON_MOVE_LIST['Attribute']


def lower_case_globals():
    """
    Returns all globals but in lower case
    :return:
    """
    return {global_var: globals()[global_var] for global_var in globals()}


def sql_to_pandas_with_vars(sql: str):
    """
    Preset with data in SqlToPandas class
    :param sql: Sql query
    :return: SqlToPandasClass with
    """
    return SqlToPandas(sql, lower_case_globals()).data_frame


def test_for_multiple_statements():
    """
    Test that exception is raised when there are multiple queries
    :return:
    """
    sql = 'select * from foo; select * from bar;'
    try:
        sql_to_pandas_with_vars(sql)
    except Exception as err:
        assert isinstance(err, MultipleQueriesException)


def test_for_valid_query():
    """
    Test that exception is raised for invalid query
    :return:
    """
    sql = "hello world!"
    try:
        sql_to_pandas_with_vars(sql)
    except InvalidQueryException as err:
        assert isinstance(err, InvalidQueryException)


def test_select_star():
    """
    Tests the simple select * case
    :return:
    """
    myframe = sql_to_pandas_with_vars("select * from forest_fires")
    assert FOREST_FIRES.equals(myframe)


def test_case_insensitivity():
    """
    Tests to ensure that the sql is case insensitive for table names
    :return:
    """
    assert FOREST_FIRES.equals(sql_to_pandas_with_vars("select * from FOREST_fires"))


def test_select_specific_fields():
    """
    Tests selecting specific fields
    :return:
    """
    myframe = sql_to_pandas_with_vars("select temp,RH,wind,rain as water,area from forest_fires")
    pandas_frame = FOREST_FIRES[['temp', 'RH', 'wind', 'rain', 'area']].rename(columns={'rain': 'water'})
    assert myframe.equals(pandas_frame)


def test_type_conversion():
    """
    Tests sql as statements
    :return:
    """
    my_frame = sql_to_pandas_with_vars("""select cast(temp as int64),cast(RH as float64) my_rh, wind, rain, area,
    cast(2 as int64) my_num from forest_fires""")
    fire_frame = FOREST_FIRES[['temp', 'RH', 'wind', 'rain', 'area']].rename(columns={'RH': 'my_rh'})
    fire_frame["my_num"] = 2
    pandas_frame = fire_frame.astype({'temp': 'int64', 'my_rh': 'float64', 'my_num': 'int64'})
    assert pandas_frame.equals(my_frame)


def test_for_non_existent_table():
    """
    Check that exception is raised if table does not exist
    :return:
    """
    try:
        sql_to_pandas_with_vars("select * from a_table_that_is_not_here")
    except Exception as err:
        assert isinstance(err, DataFrameDoesNotExist)


def test_using_math():
    """
    Test the mathematical operations and order of operations
    :return:
    """
    my_frame = sql_to_pandas_with_vars("select temp, 1 + 2 * 3 as my_number from forest_fires")
    pandas_frame = FOREST_FIRES[['temp']].copy()
    pandas_frame['my_number'] = 1 + 2 * 3
    print(pandas_frame)
    assert pandas_frame.equals(my_frame)


def test_distinct():
    """
    Test use of the distinct keyword
    :return:
    """
    my_frame = sql_to_pandas_with_vars("select distinct area, rain from forest_fires")
    pandas_frame = FOREST_FIRES[['area', 'rain']].copy()
    pandas_frame.drop_duplicates(keep='first', inplace=True)
    pandas_frame.reset_index(inplace=True)
    pandas_frame.drop(columns='index', inplace=True)
    assert pandas_frame.equals(my_frame)


def test_subquery():
    """
    Test ability to perform subqueries
    :return:
    """
    my_frame = sql_to_pandas_with_vars("select * from (select area, rain from forest_fires) rain_area")
    pandas_frame = FOREST_FIRES[['area', 'rain']].copy()
    assert pandas_frame.equals(my_frame)


def test_join_no_inner():
    """
    Test join
    :return:
    """
    my_frame = sql_to_pandas_with_vars(
        """select * from digimon_mon_list join
            digimon_move_list
            on digimon_mon_list.attribute = digimon_move_list.attribute""")
    pandas_frame1 = DIGIMON_MON_LIST
    pandas_frame2 = DIGIMON_MOVE_LIST
    merged_frame = pandas_frame1.merge(pandas_frame2, on="Attribute")
    assert merged_frame.equals(my_frame)


def test_join_wo_specifying_table():
    """
    Test join where table isn't specified in join
    :return:
    """
    my_frame = sql_to_pandas_with_vars(
        """
        select * from digimon_mon_list join
        digimon_move_list
        on mon_attribute = move_attribute
        """)
    pandas_frame1 = DIGIMON_MON_LIST
    pandas_frame2 = DIGIMON_MOVE_LIST
    merged_frame = pandas_frame1.merge(pandas_frame2, left_on="mon_attribute", right_on="move_attribute")
    assert merged_frame.equals(my_frame)


def test_join_w_inner():
    """
    Test join
    :return:
    """
    my_frame = sql_to_pandas_with_vars(
        """select * from digimon_mon_list inner join
            digimon_move_list
            on digimon_mon_list.attribute = digimon_move_list.attribute""")
    pandas_frame1 = DIGIMON_MON_LIST
    pandas_frame2 = DIGIMON_MOVE_LIST
    merged_frame = pandas_frame1.merge(pandas_frame2, on="Attribute")
    assert merged_frame.equals(my_frame)


def test_outer_join_no_outer():
    """
    Test outer join
    :return:
    """
    my_frame = sql_to_pandas_with_vars(
        """select * from digimon_mon_list full outer join
            digimon_move_list
            on digimon_mon_list.type = digimon_move_list.type""")
    pandas_frame1 = DIGIMON_MON_LIST
    pandas_frame2 = DIGIMON_MOVE_LIST
    merged_frame = pandas_frame1.merge(pandas_frame2, how="outer", on="Type")
    assert merged_frame.equals(my_frame)


def test_outer_join_w_outer():
    """
    Test outer join
    :return:
    """
    my_frame = sql_to_pandas_with_vars(
        """select * from digimon_mon_list full join
            digimon_move_list
            on digimon_mon_list.type = digimon_move_list.type""")
    pandas_frame1 = DIGIMON_MON_LIST
    pandas_frame2 = DIGIMON_MOVE_LIST
    merged_frame = pandas_frame1.merge(pandas_frame2, how="outer", on="Type")
    assert merged_frame.equals(my_frame)


def test_left_joins():
    """
    Test right, left, inner, and outer joins
    :return:
    """
    my_frame = sql_to_pandas_with_vars(
        """select * from digimon_mon_list left join
            digimon_move_list
            on digimon_mon_list.type = digimon_move_list.type""")
    pandas_frame1 = DIGIMON_MON_LIST
    pandas_frame2 = DIGIMON_MOVE_LIST
    merged_frame = pandas_frame1.merge(pandas_frame2, how="left", on="Type")
    assert merged_frame.equals(my_frame)


def test_left_outer_joins():
    """
    Test right, left, inner, and outer joins
    :return:
    """
    my_frame = sql_to_pandas_with_vars(
        """select * from digimon_mon_list left outer join
            digimon_move_list
            on digimon_mon_list.type = digimon_move_list.type""")
    pandas_frame1 = DIGIMON_MON_LIST
    pandas_frame2 = DIGIMON_MOVE_LIST
    merged_frame = pandas_frame1.merge(pandas_frame2, how="left", on="Type")
    assert merged_frame.equals(my_frame)


def test_right_joins():
    """
    Test right, left, inner, and outer joins
    :return:
    """
    my_frame = sql_to_pandas_with_vars(
        """select * from digimon_mon_list right join
            digimon_move_list
            on digimon_mon_list.type = digimon_move_list.type""")
    pandas_frame1 = DIGIMON_MON_LIST
    pandas_frame2 = DIGIMON_MOVE_LIST
    merged_frame = pandas_frame1.merge(pandas_frame2, how="right", on="Type")
    assert merged_frame.equals(my_frame)


def test_right_outer_joins():
    """
    Test right, left, inner, and outer joins
    :return:
    """
    my_frame = sql_to_pandas_with_vars(
        """select * from digimon_mon_list right outer join
            digimon_move_list
            on digimon_mon_list.type = digimon_move_list.type""")
    pandas_frame1 = DIGIMON_MON_LIST
    pandas_frame2 = DIGIMON_MOVE_LIST
    merged_frame = pandas_frame1.merge(pandas_frame2, how="right", on="Type")
    assert merged_frame.equals(my_frame)


def test_cross_joins():
    """
    Test right, left, inner, and outer joins
    :return:
    """
    my_frame = sql_to_pandas_with_vars(
        """select * from digimon_mon_list cross join
            digimon_move_list
            on digimon_mon_list.type = digimon_move_list.type""")
    pandas_frame1 = DIGIMON_MON_LIST
    pandas_frame2 = DIGIMON_MOVE_LIST
    merged_frame = pandas_frame1.merge(pandas_frame2, how="outer", on="Type")
    assert merged_frame.equals(my_frame)


def test_group_by():
    """
    Test group by constraint
    :return:
    """
    my_frame = sql_to_pandas_with_vars("""select month, day from forest_fires group by month, day""")
    pandas_frame = FOREST_FIRES.groupby(["month", "day"]).size().to_frame('size').reset_index().drop(columns=['size'])
    assert pandas_frame.equals(my_frame)


def test_avg():
    """
    Test the avg
    :return:
    """
    my_frame = sql_to_pandas_with_vars("select avg(temp) from forest_fires")
    pandas_frame = FOREST_FIRES.agg({'temp': np.mean}).to_frame('mean_temp').reset_index().drop(columns=['index'])
    assert pandas_frame.equals(my_frame)

def test_sum():
    """
    Test the sum
    :return:
    """
    my_frame = sql_to_pandas_with_vars("select sum(temp) from forest_fires")
    pandas_frame = FOREST_FIRES.agg({'temp': np.sum}).to_frame('sum_temp').reset_index().drop(columns=['index'])
    assert pandas_frame.equals(my_frame)


def test_max():
    """
    Test the max
    :return:
    """
    my_frame = sql_to_pandas_with_vars("select max(temp) from forest_fires")
    pandas_frame = FOREST_FIRES.agg({'temp': np.max}).to_frame('max_temp').reset_index().drop(columns=['index'])
    assert pandas_frame.equals(my_frame)

def test_min():
    """
    Test the min
    :return:
    """
    my_frame = sql_to_pandas_with_vars("select min(temp) from forest_fires")
    pandas_frame = FOREST_FIRES.agg({'temp': np.min}).to_frame('min_temp').reset_index().drop(columns=['index'])
    assert pandas_frame.equals(my_frame)

def test_multiple_aggs():
    """
    Test multiple aggregations
    :return:
    """
    my_frame = sql_to_pandas_with_vars("select min(temp), max(temp), avg(temp), max(wind) from forest_fires")
    pandas_frame = FOREST_FIRES.copy()
    pandas_frame['min_temp'] = FOREST_FIRES.temp.copy()
    pandas_frame['max_temp'] = FOREST_FIRES.temp.copy()
    pandas_frame['mean_temp'] = FOREST_FIRES.temp.copy()
    pandas_frame = pandas_frame.agg({'min_temp': np.min, 'max_temp': np.max, 'mean_temp': np.mean, 'wind': np.max})
    pandas_frame.rename({'wind': 'max_wind'}, inplace=True)
    pandas_frame = pandas_frame.to_frame().transpose()
    assert pandas_frame.equals(my_frame)


def test_agg_w_groupby():
    """
    Test using aggregates and group by together
    :return:
    """
    my_frame = sql_to_pandas_with_vars("select day, month, min(temp), max(temp) from forest_fires group by day, month")
    pandas_frame = FOREST_FIRES.copy()
    pandas_frame['min_temp'] = pandas_frame.temp
    pandas_frame['max_temp'] = pandas_frame.temp
    pandas_frame = pandas_frame.groupby(["day", "month"]).aggregate({'min_temp': np.min, 'max_temp': np.max})\
        .reset_index()
    assert pandas_frame.equals(my_frame)


def test_where_clause():
    """
    Test where clause
    :return:
    """
    my_frame = sql_to_pandas_with_vars("""select * from forest_fires where month = 'mar'""")
    pandas_frame = FOREST_FIRES.copy()
    pandas_frame = pandas_frame[pandas_frame.month == 'mar']
    assert pandas_frame.equals(my_frame)


def test_order_by():
    """
    Test order by clause
    :return:
    """
    my_frame = sql_to_pandas_with_vars("""select * from forest_fires order by temp desc, wind asc, area""")
    pandas_frame = FOREST_FIRES.copy()
    pandas_frame.sort_values(by=['temp', 'wind', 'area'], ascending=[0, 1, 1], inplace=True)
    assert pandas_frame.equals(my_frame)


def test_limit():
    """
    Test limit clause
    :return:
    """
    my_frame = sql_to_pandas_with_vars("""select * from forest_fires limit 10""")
    pandas_frame = FOREST_FIRES.copy().head(10)
    assert pandas_frame.equals(my_frame)


def test_having():
    """
    Test having clause
    :return:
    """
    my_frame = sql_to_pandas_with_vars("select min(temp) from forest_fires having min(temp) > 2")
    pandas_frame = FOREST_FIRES.copy()
    pandas_frame['min_temp'] = FOREST_FIRES['temp']
    aggregated_df = pandas_frame.aggregate({'min_temp': 'min'}).to_frame().transpose()
    pandas_frame = aggregated_df[aggregated_df['min_temp'] > 2]
    assert pandas_frame.equals(my_frame)


def test_having_with_group_by():
    """
    Test having clause
    :return:
    """
    my_frame = sql_to_pandas_with_vars("select day, min(temp) from forest_fires group by day having min(temp) > 5")
    pandas_frame = FOREST_FIRES.copy()
    pandas_frame['min_temp'] = FOREST_FIRES['temp']
    pandas_frame = pandas_frame[['day', 'min_temp']].groupby('day').aggregate({'min_temp': np.min})
    pandas_frame = pandas_frame[pandas_frame['min_temp'] > 5].reset_index()
    print(pandas_frame)
    assert pandas_frame.equals(my_frame)


def test_operations_between_columns_and_numbers():
    """
    Tests operations between columns
    :return:
    """
    my_frame = sql_to_pandas_with_vars("""select temp * wind + rain / dmc + 37 from forest_fires""")
    pandas_frame = FOREST_FIRES.copy()
    pandas_frame['temp_mul_wind_add_rain_div_dmc_add_37'] = pandas_frame['temp'] * pandas_frame['wind'] + \
                                                            pandas_frame['rain'] / pandas_frame['DMC'] + 37
    pandas_frame = pandas_frame['temp_mul_wind_add_rain_div_dmc_add_37'].to_frame()
    assert pandas_frame.equals(my_frame)


def test_select_star_from_multiple_tables():
    """
    Test selecting from two different tables
    :return:
    """
    my_frame = sql_to_pandas_with_vars("""select * from forest_fires, digimon_mon_list""")
    forest_fires = FOREST_FIRES.copy()
    digimon_mon_list_new = DIGIMON_MON_LIST.copy()
    forest_fires['_temp_id'] = 1
    digimon_mon_list_new['_temp_id'] = 1
    pandas_frame = merge(forest_fires, digimon_mon_list_new, on='_temp_id').drop(columns=['_temp_id'])
    assert pandas_frame.equals(my_frame)


def test_select_columns_from_two_tables_with_same_column_name():
    """
    Test selecting tables
    :return:
    """
    my_frame = sql_to_pandas_with_vars("""select * from forest_fires table1, forest_fires table2""")
    table1 = FOREST_FIRES.copy()
    table2 = FOREST_FIRES.copy()
    table1['_temp_id'] = 1
    table2['_temp_id'] = 1
    pandas_frame = merge(table1, table2, on='_temp_id').drop(columns=['_temp_id'])
    assert pandas_frame.equals(my_frame)


def test_maintain_case_in_query():
    """
    Test nested subqueries
    :return:
    """
    my_frame = sql_to_pandas_with_vars(
        """select wind, rh from forest_fires""")
    pandas_frame = FOREST_FIRES.copy()[['wind', 'RH']].rename(columns={"RH": "rh"})
    assert pandas_frame.equals(my_frame)


def test_nested_subquery():
    """
    Test nested subqueries
    :return:
    """
    my_frame = sql_to_pandas_with_vars(
        """select * from
            (select wind, rh from
              (select * from forest_fires) fires) wind_rh""")
    pandas_frame = FOREST_FIRES.copy()[['wind', 'RH']].rename(columns={"RH": "rh"})
    assert pandas_frame.equals(my_frame)


def test_union():
    """
    Test union in queries
    :return:
    """
    my_frame = sql_to_pandas_with_vars("""
    select * from forest_fires order by wind desc limit 5
     union 
    select * from forest_fires order by wind asc limit 5
    """)
    pandas_frame1 = FOREST_FIRES.copy().sort_values(by=['wind'], ascending=[False]).head(5)
    pandas_frame2 = FOREST_FIRES.copy().sort_values(by=['wind'], ascending=[True]).head(5)
    pandas_frame = concat([pandas_frame1, pandas_frame2], ignore_index=True).drop_duplicates().reset_index(drop=True)
    assert pandas_frame.equals(my_frame)

def test_union_distinct():
    """
    Test union distinct in queries
    :return:
    """
    my_frame = sql_to_pandas_with_vars("""
        select * from forest_fires order by wind desc limit 5
         union distinct
        select * from forest_fires order by wind asc limit 5
        """)
    pandas_frame1 = FOREST_FIRES.copy().sort_values(by=['wind'], ascending=[False]).head(5)
    pandas_frame2 = FOREST_FIRES.copy().sort_values(by=['wind'], ascending=[True]).head(5)
    pandas_frame = concat([pandas_frame1, pandas_frame2], ignore_index=True).drop_duplicates().reset_index(drop=True)
    assert pandas_frame.equals(my_frame)

def test_union_all():
    """
    Test union distinct in queries
    :return:
    """
    my_frame = sql_to_pandas_with_vars("""
        select * from forest_fires order by wind desc limit 5
         union all
        select * from forest_fires order by wind asc limit 5
        """)
    pandas_frame1 = FOREST_FIRES.copy().sort_values(by=['wind'], ascending=[False]).head(5)
    pandas_frame2 = FOREST_FIRES.copy().sort_values(by=['wind'], ascending=[True]).head(5)
    pandas_frame = concat([pandas_frame1, pandas_frame2], ignore_index=True).reset_index(drop=True)
    print(pandas_frame)
    assert pandas_frame.equals(my_frame)

def test_intersect_distinct():
    """
    Test union distinct in queries
    :return:
    """
    my_frame = sql_to_pandas_with_vars("""
            select * from forest_fires order by wind desc limit 5
             intersect distinct
            select * from forest_fires order by wind desc limit 3
            """)
    pandas_frame1 = FOREST_FIRES.copy().sort_values(by=['wind'], ascending=[False]).head(5)
    pandas_frame2 = FOREST_FIRES.copy().sort_values(by=['wind'], ascending=[False]).head(3)
    pandas_frame = merge(left=pandas_frame1, right=pandas_frame2, how='inner', on=list(pandas_frame1.columns))
    assert pandas_frame.equals(my_frame)

def test_except_distinct():
    """
    Test except distinct in queries
    :return:
    """
    my_frame = sql_to_pandas_with_vars("""
                select * from forest_fires order by wind desc limit 5
                 except distinct
                select * from forest_fires order by wind desc limit 3
                """)
    pandas_frame1 = FOREST_FIRES.copy().sort_values(by=['wind'], ascending=[False]).head(5)
    pandas_frame2 = FOREST_FIRES.copy().sort_values(by=['wind'], ascending=[False]).head(3)
    pandas_frame = pandas_frame1[~pandas_frame1.isin(pandas_frame2).all(axis=1)].drop_duplicates().reset_index(
        drop=True)
    assert pandas_frame.equals(my_frame)

def test_except_all():
    """
    Test except distinct in queries
    :return:
    """
    my_frame = sql_to_pandas_with_vars("""
                select * from forest_fires order by wind desc limit 5
                 except all
                select * from forest_fires order by wind desc limit 3
                """)
    pandas_frame1 = FOREST_FIRES.copy().sort_values(by=['wind'], ascending=[False]).head(5)
    pandas_frame2 = FOREST_FIRES.copy().sort_values(by=['wind'], ascending=[False]).head(3)
    pandas_frame = pandas_frame1[~pandas_frame1.isin(pandas_frame2).all(axis=1)].reset_index(drop=True)
    assert pandas_frame.equals(my_frame)

if __name__ == "__main__":
    test_union_all()