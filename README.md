<h1> Pundit </h1>

Code commenting has become a obsolute need for any of the projects you work. There are many tools out there which helps
you to document from the comments in file directly like sphinx (https://www.sphinx-doc.org/en/master/). This project is
aimed at easing the code commenting.  

for example:

You write a function called
```
void func(int a, int b)
{
     ....
}
```

Pundit will translate the above code as
```
/**
 * func() -
 * @a:
 * @b:
 *
 *
 *
 * Context:
 * Return:
 */
 void func(int a, int b)
{
      ....
}
 ```
    
Pundit lets you to update the comment even when there is change in function prototype.
Now you wish to add extra argument called "c"
```
/**
 * func() - function name
 * @a: arg1
 * @b: arg2
 *
 * sample function
 *
 * Context:
 * Return: void
 */
 void func(int a, int b, int c)
{
      ....
}
```
Lets pundIT now

```
/**
 * func() -
 * @a:
 * @b:
 * @c:
 *
 *
 *
 * Context:
 * Return:
 */
 void func(int a, int b, int c)
{
      ....
}
```

Pundit lets all the description updated in the comment stay intact.

This is based entirely based on guidleines given on <b> https://www.kernel.org/doc/html/latest/doc-guide/kernel-doc.html </b>

This can be done by simply running
```
python pundit.py -f <your_file.c>
```

Pundit also lets you to check whether a c file has proper commenting as well
```
python pundit.py -c <your_file.c>
```

Support if you had
```
/**
 * f() -
 * @a:
 *
 *
 *
 * Context:
 * Return:
 */
void func(int a, int b)
{

}
```

Pundit displays:
```
Found errors or warnings for target 'func' at line:22
ERROR: Missing or incorrect header name 'func' found: f()
ERROR: Missing description for member 'a'
ERROR: Missing one or more members: 'b'
WARNING: No description found for the target
WARNING: Missing description for 'Context'
ERROR: Missing description for 'Return
```
