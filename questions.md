1. Discuss your strategy and decisions implementing the application. Please, consider time
   complexity, effort cost, technologies used and any other variable that you understand
   important on your development process:

First my decision to pick Django was based on the fact that python is really good manipulating files thanks to its libraries (pandas in this case). Also, Django is a really good framework to build web applications fast and with a lot of built-in functionalities (even though the simplicity of the project wasn't asking for something so powerfull) that would take a lot of time to implement from scratch in nodejs or nextjs for example, also node is not the best in terms of manipulating files (specially csv). And because it's the framework used in the company.

I've chosed to create a data service (using Service Layer Pattern), to manipulate the csv files, using benefits like separation of concerns, testability, future extensibility.
I've also decided to create an abstract class (BaseCSVService), that way in case the data source changes in the future for a SQL database for example, it would be necessary to change just in one place and implement the database service... it won't be necessary to change it anywhere else, since the views will always call the methods from the abstract class.

I've also decided to use cache in some methods, since the csv file data won't change during the execution of the application, that way I avoid reprocessing the data every time a request is made, improving performance (O(1) after first load instead of O(n) on every request). This could cost some Memory usage for performance gain, but since the data is not that big, I think it's a good trade-off in my opinion.

There also some helpers methods, for example to create links, that way if the formatting needs to change in the future, it would be necessary to change just in one place, and it's easier to read the code and to reuse it instead of coding the same things over and over. Also the extension for new columns is easy as I show in question 2.

And for last I chose to use docker because it's easier to set up the development environment, avoiding the "it works on my machine" problem things, especially given Python's complex dependency management with pip, pipenv, PyPI, pythons version, etc. And it also makes the application more portable and easier to deploy in different environments.

1. How would you change your solution to account for future columns that might be
   requested, such as “Bill Voted On Date” or “Co-Sponsors”?

Considering I'm currently selecting the columns and renaming them manually (also making some of them clickable, adding styles etc), I could add this new columns in both ways I show below:

Example:

```
def get_complete_bills_data(self):
...
       base_output = {
            'id': result['id'],
            'title': result['title_formatted'],
            'sponsor': result['sponsor_formatted'],
            'total_votes': result['total_votes'],
            'yea_votes': result['yea_votes'],
            'nay_votes': result['nay_votes'],
        }

        ########## add new columns ###########
        # 1. Add specific columns if they exist, in case they don't it won't break
        if 'co_sponsor' in result.columns:
            base_output['co_sponsor'] = result['co_sponsor']

        if 'vote_date' in result.columns:
            base_output['vote_date'] = result['vote_date_formatted'] if 'vote_date_formatted' in result.columns else result['vote_date']

        # 2. or, more generically, I could loop through all columns in the bills dataframe and add them if they are not already in the base_output
         extra_columns = [col for col in self.bills.columns if col not in [
             'id', 'title', 'sponsor_id']]
         for col in extra_columns:
             if col in result.columns:
                 # Use formatted version if it exists, otherwise use raw
                 formatted_col = f'{col}_formatted'
                 base_output[col] = result[formatted_col] if formatted_col in result.columns else result[col]
```

3. How would you change your solution if instead of receiving CSVs of data, you were given a
   list of legislators or bills that you should generate a CSV for?

Considering this reverse scenario, I would create a service file in the service layer to handle the CSV generation.

```
# I could make it more generic, but I rather keep it one responsibility per class, even if I need a pdf export in the future I would create another class for that, this also makes the config and dependencies easier to manage
class DataExportToCSVService:
    def export_legislators_to_csv(self, legislators: List[Legislator]) -> str:
    def export_bills_to_csv(self, bills: List[Bill]) -> str:
    def export_votes_to_csv(self, votes: List[Vote]) -> str:
```

This method would take a list of legislators or bills as input, make a schema validation and convert it into a pandas DataFrame, and then use pandas' built-in functionality to export the DataFrame to a CSV file.

```
  df = pd.DataFrame(data)
  df.to_csv('output.csv', index=False)
```

4. How long did you spend working on the assignment?
   I think around 3-4 hours because of some refactors to create nicers layout and styles and to make the code cleaner and more maintainable.
