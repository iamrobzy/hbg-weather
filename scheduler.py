import modal

app = modal.App('scheduler')

@app.function(schedule=modal.Period(minutes=1))
def update():
    print('Updating...')