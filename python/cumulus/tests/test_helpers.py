# snowmelt/tests.py
import unittest
import datetime

from context import (
    config,
    helpers
)


class Test_snodas_get_raw_infile(unittest.TestCase):

    def test_infile_type_unmasked(self):
        """unmasked filename is correct"""

        dt = datetime.datetime(year=2019, month=1, day=1)

        self.assertEqual(
            'SNODAS_unmasked_20190101.tar',
            helpers.snodas_get_raw_infile_name(dt, 'unmasked')
        )
    
    def test_infile_type_unmasked_badcase(self):
        """unmasked filename is correct regardless of infile_type string case"""

        dt = datetime.datetime(year=2019, month=1, day=1)

        self.assertEqual(
            'SNODAS_unmasked_20190101.tar',
            helpers.snodas_get_raw_infile_name(dt, 'UnMasked')
        )
    
    def test_infile_type_masked(self):
        """masked filename is correct"""

        dt = datetime.datetime(year=2019, month=1, day=1)

        self.assertEqual(
            'SNODAS_20190101.tar',
            helpers.snodas_get_raw_infile_name(dt, 'masked')
        )
    
    def test_infile_type_masked_badcase(self):
        """masked filename is correct regardless of infile_type string case"""

        dt = datetime.datetime(year=2019, month=1, day=1)

        self.assertEqual(
            'SNODAS_20190101.tar',
            helpers.snodas_get_raw_infile_name(dt, 'Masked')
        )


# class Test_get_ds_type(unittest.TestCase):


#     def test_before_20110124_returns_us(self):
#         """Before January 24, 2011 return value should be 'us'"""
        
#         dt = datetime.datetime(2000, 1, 1)  # January 01, 2000
#         self.assertEqual(get_ds_type(dt), 'us')


#     def test_after_20110124_returns_us(self):
#         """After January 24, 2011 return value should be 'zz'"""
        
#         dt = datetime.datetime(2019, 1, 1)  # January 01, 2019
#         self.assertEqual(get_ds_type(dt), 'zz')


# class Test_get_nodata_value(unittest.TestCase):


#     def test_before_20110124_returns_55537(self):
#         """Before January 24, 2011 return value should be 55537"""

#         dt = datetime.datetime(2000, 1, 1)  # January 01, 2000
#         self.assertEqual(get_nodata_value(dt), '55537')


#     def test_after_20110124_returns_us(self):
#         """After January 24, 2011 return value should be 55537"""
        
#         dt = datetime.datetime(2019, 1, 1)  # January 01, 2019
#         self.assertEqual(get_nodata_value(dt), '-9999')


# class Test_file_needs_lakefix(unittest.TestCase):


#     def test_after_2014_varcode_1034(self):

#         dt = datetime.datetime(2019, 1, 1)
#         varcode = '1034'

#         self.assertTrue(file_needs_lakefix(dt, varcode))


#     def test_after_2014_varcode_1034asInt(self):
#         '''snowmelt only passes varcode as string; however, make sure
#         function still works as designed if varcode passed as int
#         '''

#         dt = datetime.datetime(2019, 1, 1)
#         varcode = 1034

#         self.assertTrue(file_needs_lakefix(dt, varcode))


#     def test_after_2014_varcode_1036(self):

#         dt = datetime.datetime(2019, 1, 1)
#         varcode = '1036'

#         self.assertTrue(file_needs_lakefix(dt, varcode))


#     def test_after_2014_varcode_bogusnumber(self):

#         dt = datetime.datetime(2019, 1, 1)
#         varcode = '100000'

#         self.assertFalse(file_needs_lakefix(dt, varcode))


#     def test_before_2014_varcode_1034(self):

#         dt = datetime.datetime(2013, 1, 1)
#         varcode = '1034'

#         self.assertFalse(file_needs_lakefix(dt, varcode))


#     def test_before_2014_varcode_1034asInt(self):
#         '''snowmelt only passes varcode as string; however, make sure
#         function still works as designed if varcode passed as int
#         '''

#         dt = datetime.datetime(2013, 1, 1)
#         varcode = 1034

#         self.assertFalse(file_needs_lakefix(dt, varcode))


#     def test_before_2014_varcode_1036(self):

#         dt = datetime.datetime(2013, 1, 1)
#         varcode = '1036'

#         self.assertFalse(file_needs_lakefix(dt, varcode))


#     def test_before_2014_varcode_bogusnumber(self):

#         dt = datetime.datetime(2013, 1, 1)
#         varcode = '100000'

#         self.assertFalse(file_needs_lakefix(dt, varcode))


if __name__ == "__main__":
    unittest.main(verbosity=2)
