import pandas as pd
import numpy as np
from lxml import etree as ET


class NestedTable():

    def __init__(self, dict_df, decimal_places=8):

        """
        dict_df (dict): A dictionary containing the table name and the DataFrame and groups_information. {str : [pd.DataFrame, dict] , str: [pd.DataFrame, dict], ...}
        The groups_information is a dictionary containing the group name and the group values. {str: [str, str, ...], str: [str, str, ...], ...}
        """
        self.original_df = dict_df
        self.decimal_places = decimal_places

    def to_xml(self, input_prism_template, output_file):

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
        
        # creating tables
        table_id = 0
        for table_name, dict_df in self.original_df.items():
            
            
            # print(dict_group.values())
            num_subcolumns = dict_df[list(dict_df.keys())[0]].shape[1]
            
            table = ET.SubElement(root, "Table", {"ID": "Table{}".format(table_id), 
                                                  "YFormat":"replicates", 
                                                  "Replicates":"{}".format(num_subcolumns), 
                                                  "TableType":"TwoWay", 
                                                  "ExtTableType":"Nested", 
                                                  "EVFormat": "AsteriskAfterNumber"})
            title = ET.SubElement(table, "Title")
            title.text = table_name
            table_id += 1
            
            # adding subcolumn titles, we have to add sub columns upfront before populating the data
            # XML format is lttle wierd, first column of every group and then second column of every group and so on.
            # <SubColumnTitles OwnSet="1">
            # <Subcolumn>
            # <d><TextAlign align="Center">Herd 1</TextAlign></d>
            # <d><TextAlign align="Center">Herd 4</TextAlign></d>
            # <d><TextAlign align="Center">Herd 7</TextAlign></d>
            # </Subcolumn>
            # <Subcolumn>
            # <d><TextAlign align="Center">Herd 2</TextAlign></d>
            # <d><TextAlign align="Center">Herd 5</TextAlign></d>
            # <d><TextAlign align="Center">Herd 8</TextAlign></d>
            # </Subcolumn>
            # <Subcolumn>
            # <d><TextAlign align="Center">Herd 3</TextAlign></d>
            # <d><TextAlign align="Center">Herd 6</TextAlign></d>
            # <d><TextAlign align="Center">Herd 9</TextAlign></d>
            # </Subcolumn>
            # </SubColumnTitles>
                        
            lst_all_groups = []
            for group_name, group_df in dict_df.items():
                lst_all_groups.append(list(group_df.columns))
                
            np_all_groups = np.array(lst_all_groups)
            subcolumntitles = ET.SubElement(table, "SubColumnTitles", {"OwnSet" : "1"})
            
            for i in range(num_subcolumns):
                sub_column = ET.SubElement(subcolumntitles, "Subcolumn")
                cols = np_all_groups[:, i]
                for col in cols:
                    d = ET.SubElement(sub_column, "d")
                    sub_col_name = ET.SubElement(d, "TextAlign", {"Align": "Center"})
                    sub_col_name.text = col
                    
            # populating the data
            
            for group_name, group_df in dict_df.items():
                
                Ycolumn = ET.SubElement(table, "YColumn", {"Width": "81", "Decimals" : "{}".format(self.decimal_places), "Subcolumns": "{}".format(num_subcolumns) })
                title = ET.SubElement(Ycolumn,  "Title")
                title.text = "{}".format(group_name)

                for col in group_df.columns:
                    subcolumn = ET.SubElement(Ycolumn, "Subcolumn")
                    for val in group_df[col].values:
                        record = ET.SubElement(subcolumn, "d")
                        record.text = str(val)

                
        # writing the dataframe to prism file
        prism_tree.write(output_file, pretty_print=True, xml_declaration=True, encoding="utf-8")
        
        
if __name__ == '__main__':
        
        # How to use?
        
        arr = np.random.randint(0, 100, (5, 3))
        # df = pd.DataFrame(arr, columns=[f'Herd {i}' for i in range(10)])
        cow_treated_df = pd.DataFrame(arr, columns=[f'Herd {i}' for i in range(3)])
        cow_untreated_df = pd.DataFrame(arr, columns=[f'Herd {i}' for i in range(3)])
        cow_control_df = pd.DataFrame(arr, columns=[f'Herd {i}' for i in range(3)])
        
        pig_treated_df = pd.DataFrame(arr, columns=[f'Herd {i}' for i in range(3)])
        pig_untreated_df = pd.DataFrame(arr, columns=[f'Herd {i}' for i in range(3)])
        pig_control_df = pd.DataFrame(arr, columns=[f'Herd {i}' for i in range(3)])
        
        print(pig_control_df)
        dict_df = {"Cow Treatment": {"Untreated": cow_untreated_df, "Treated": cow_treated_df , "Control": cow_control_df},
                   "pig Treatment": {"Untreated":pig_treated_df, "Treated": pig_untreated_df, "Control": pig_control_df}}
        nested_table = NestedTable(dict_df)
        nested_table.to_xml("data/prism_template.pzfx", "data/populated_nested.pzfx")
        print("XML file created successfully.")


        
