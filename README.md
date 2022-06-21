# Kotaz Utils

## О проекте

Проект содержит набор инструментов для упрощения написания проектов. Не в вашем случае ❤️

## Kotazy Lang

Немного о Kotazy Lang. Это на данный момент интерпретируемый язык программирования.  
Его работа базируется на 4х понятиях - константа, вызов, блок и идентификатор.  
`abc` - идентификатор  
`1`, `1.1`, `-1.1`, `"abc"` - константа. Поддерживается только float и string.  
`идентификатор(аргументы, ...)` - вызов  
`{вызов; вызов; ...}` - блок  
Аргументом является ВСЕ, что угодно - новый блок, вызов, константа или идентификатор.  
Программа начинается с главного блока, в него помещаются все вызовы. На данный момент проект поддерживает лишь парочку операций.  

```plaintext
{
    set(test, 123);
    out("Hello world", test);
    set(foo, {out(123); ret(1)});/*123*/
    out(foo);
    def(boo, {out(456); ret(1)});
    out(boo);
    boo();
    out(out, ecl, pcl);
    pcl("2+2*2")
}
```

**Разбор построчно:**
`set(test, 123);` - устанавливаем переменную `test` в значение `123`  
`out("Hello world", test);` - выводим строку `Hello world` и значение переменной `test`  
`set(foo, {out(123); ret(1)});/*123*/` - выполняем блок, выводим `123` и возвращаем значение `1`, которое сохраняется в переменную `foo`  
`out(foo);` - выводим значение переменной `foo` - `1`  
`def(boo, {out(456); ret(1)});` - а вот тут теперь создаем функцию `boo`, которая выводит `456` и возвращает значение `1`  
`out(boo);` - выводим, что это функция `boo`  
`boo();` - выполняем функцию `boo`  
`out(out, ecl, pcl);` - выводим парочку базовых функций  
`pcl("2+2*2")` - выводим результат вычисления выражения `2+2*2`  
P.S. Комментарии в любом месте кода - `/* 123 */`  
P.P.S. все аргументы разделяются запятой, а вызовы разделяются точкой с запятой. Не оставляйте лишних знаков в конце кода.  

**Вот вывод:**

```py
Hello world 123.0
123.0
1.0
<function boo>
456.0
<function out> <function ecl> <function pcl>
6
```

| Функция | Расшифровка             | Описание                                                                                    | Аргументы                       | Возвращает    | Пример                         |
| ------- | ----------------------- | ------------------------------------------------------------------------------------------- | ------------------------------- | ------------- | ------------------------------ |
| `out`   | out                     | Выводит строку в консоль.                                                                   | `[text:any...]`                 | `none`        | `out("Hello, ", name)`         |
| `set`   | set                     | Устанавливает значение переменной.                                                          | `{identifier:id}, {value:any}`  | `none`        | `set(test, 123)`               |
| `ret`   | return                  | Возвращает значение. Позволяет превратить любую константу в вызов. Равноценно `lambda x: x` | `{value:any}`                   | `{value:any}` | `ret(1)`                       |
| `def`   | define                  | Создает функцию.                                                                            | `{identifier:id}, {body:block}` | `none`        | `def(boo, {out(456); ret(1)})` |
| `lse`   | list system environment | Выводит список переменных.                                                                  | `none`                          | `none`        | `lse()`                        |
| `fle`   | full list environment   | Выводит полный список переменных и их значения.                                             | `none`                          | `none`        | `fle()`                        |
| `clc`   | calculate               | Вычисляет выражение.                                                                        | `{expression:string}`           | `any`         | `clc("2+2*2")`                 |
| `pcl`   | print calculate         | Выводит результат вычисления сразу. Ничего не возвращает. Равноценно out(clc()).            | `{expression:string}`           | `none`        | `pcl("2+2*2")`                 |
| `ecl`   | evaluate calculate      | Вычисляет выражение, внутри поддерживаются переменные из кода.                              | `{expression:string}`           | `any`         | `set(a, 2);ecl("2+2*a")`       |
