import pandas as pd
import numpy as np
from lxml import etree as ET

class ColumnTable():

    """ This class takes a pandas DataFrame and converts it to a table in XML format.
     The columns are populated in the order as they appear in the DataFrame. """
    
    def __init__(self, dict_df, decimal_places=8):

        """ This method initializes the ColumnTable object.
        Parameters:
        dict_df (dict): A dictionary containing the table name and the DataFrame. {str : pd.DataFrame , str: pd.DataFrame, ...}
        decimal_places (int): The number of decimal places to round the values to. Default is 8.
        """
        self.original_df = dict_df
        self.decimal_places = decimal_places
        

    def to_xml(self, input_prism_template, output_file):

        """ This method takes a Prism template file and saves it to the output_file location.

        Parameters:
        input_prism_template (str): The path to the Prism template file.
        output_file (str): The path to the output file. 
           """

        prism_tree = ET.parse(input_prism_template)
        root = prism_tree.getroot()

        # checking if the root is a valid Prism template
        if root is None:
            raise ValueError("Invalid Prism template file.")

        # clearing all the content in the table
        
        # removing the table references found in tbale sequence
        table_sequence = prism_tree.find(".//{http://graphpad.com/prism/Prism.htm}TableSequence")
        if len(table_sequence) == 0:
            table_sequence = prism_tree.find("TableSequence")
            # print("table_sequence hit")
        
        refs = table_sequence.findall(".//{http://graphpad.com/prism/Prism.htm}Ref")
        if len(refs) == 0:
            refs = table_sequence.findall("Ref")
        for item in refs:
            table_sequence.remove(item)

        # Removing all the tables
        def remove_table(key):
            xml_tables = root.findall(key)
            if len(xml_tables) == 0:
                key = ".//{http://graphpad.com/prism/Prism.htm}"+ key
                xml_tables = root.findall(key)
            for table in xml_tables:
                root.remove(table)
            return root 
        
        remove_table("Table")
        remove_table("HugeTable")
        remove_table("Table1024")

            
        # creating tal
        table_id = 0
        for table_name, df in self.original_df.items():
            table = ET.SubElement(root, "HugeTable", {"ID": "Table{}".format(table_id), "XFormat" :"None", "TableType": "OneWay", "EVFormat":"AsteriskAfterNumber"})
            title = ET.SubElement(table, "Title")
            title.text = table_name


            for col in df.columns:

                Ycolumn = ET.SubElement(table, "YColumn", {"Width": "81", "Decimals" : "{}".format(self.decimal_places), "Subcolumns": "1" })
                title = ET.SubElement(Ycolumn,  "Title")
                title.text = "{}".format(col)
                subcolum = ET.SubElement(Ycolumn, "Subcolumn", {"Decimals" : "{}".format(self.decimal_places)})

                for value in df[col].values :
                    record = ET.SubElement(subcolum, "d")
                    record.text = str(value)

            table_id += 1
        
        # writing the dataframe to prism file
        prism_tree.write(output_file, pretty_print=True, xml_declaration=True, encoding="utf-8")

if __name__ == '__main__':

    #  How to use?

    arr = np.random.randint(0, 100, (5, 10))
    df = pd.DataFrame(arr, columns=[f'col_{i}' for i in range(10)])
    dict_df = {"Table1": df, "Table2": df, "Table3": df}    
    ct = ColumnTable(dict_df)
    ct.to_xml("data/prism_template.pzfx", "data/populated_columnar.pzfx")